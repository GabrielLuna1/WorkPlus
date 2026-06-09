import asyncio
import email
import imaplib
import re
import smtplib
from datetime import datetime, timezone
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Optional

from core.config import settings
from core.logger import logger

CREDENTIALS_FILE = Path("storage/email_credentials.json")


def _decodificar(s: bytes | str | None) -> str:
    if not s:
        return ""
    if isinstance(s, bytes):
        try:
            parts = decode_header(s)
            return "".join(
                part.decode(charset or "utf-8", errors="replace")
                if isinstance(part, bytes)
                else part
                for part, charset in parts
            )
        except Exception:
            return s.decode("utf-8", errors="replace")
    return s


def _extrair_email_de(s: str) -> str:
    match = re.search(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", s)
    return match.group(0) if match else s


class EmailManager:
    def __init__(self) -> None:
        self.imap: Optional[imaplib.IMAP4_SSL] = None
        self._connected = False

    @property
    def configured(self) -> bool:
        return bool(
            settings.email_imap_host and settings.email_user and settings.email_pass
        )

    async def connect_imap(self) -> bool:
        if self._connected and self.imap:
            try:
                self.imap.noop()
                return True
            except Exception:
                self._connected = False

        try:
            self.imap = imaplib.IMAP4_SSL(
                settings.email_imap_host,
                settings.email_imap_port or 993,
            )
            self.imap.login(settings.email_user, settings.email_pass)
            self._connected = True
            logger.info("email_manager.imap.conectado", host=settings.email_imap_host)
            return True
        except Exception as e:
            logger.error("email_manager.imap.erro_conexao", error=str(e))
            self._connected = False
            return False

    async def disconnect(self):
        if self.imap:
            try:
                self.imap.logout()
            except Exception:
                pass
            self.imap = None
            self._connected = False

    async def buscar_emails(
        self,
        pasta: str = "INBOX",
        criterio: str = "UNSEEN",
        max_emails: int = 50,
    ) -> list[dict]:
        if not await self.connect_imap():
            return []

        try:
            self.imap.select(pasta)
            _, ids = self.imap.search(None, criterio)
            if not ids[0]:
                return []

            id_lista = ids[0].split()[-max_emails:]
            resultados = []

            for msg_id in id_lista:
                _, data = self.imap.fetch(msg_id, "(RFC822)")
                raw = data[0][1] if data and data[0] else None
                if not raw:
                    continue

                msg = email.message_from_bytes(raw)
                parsed = self._parse_msg(msg)
                if parsed:
                    parsed["_uid"] = msg_id.decode()
                    resultados.append(parsed)

            return resultados

        except Exception as e:
            logger.error("email_manager.buscar.erro", error=str(e))
            return []
        finally:
            await self.disconnect()

    def _parse_msg(self, msg) -> Optional[dict]:
        try:
            assunto = _decodificar(msg["Subject"])
            de = _decodificar(msg["From"])
            para = _decodificar(msg["To"])
            data_raw = msg["Date"]

            corpo = ""
            if msg.is_multipart():
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        payload = part.get_payload(decode=True)
                        if payload:
                            corpo += payload.decode("utf-8", errors="replace")
                            break
                    elif part.get_content_type() == "text/html":
                        payload = part.get_payload(decode=True)
                        if payload:
                            corpo = payload.decode("utf-8", errors="replace")
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    corpo = payload.decode("utf-8", errors="replace")

            corpo = corpo[:5000]

            return {
                "assunto": assunto,
                "de": de,
                "de_email": _extrair_email_de(de),
                "para": para,
                "data_recebida": data_raw,
                "corpo": corpo[:1000],
                "corpo_completo": corpo,
            }
        except Exception as e:
            logger.warning("email_manager.parse.erro", error=str(e))
            return None

    def _extrair_vaga_id(self, assunto: str, corpo: str) -> Optional[str]:
        text = f"{assunto} {corpo}"
        match = re.search(r"(?:WorkHunter|job|vaga)[:\-\s]*([a-fA-F0-9]{24})", text)
        return match.group(1) if match else None

    def _detectar_tipo(self, assunto: str, de_email: str, corpo: str) -> str:
        text = f"{assunto} {corpo}".lower()

        if any(
            p in text
            for p in ["undelivered", "mail delivery failed", "bounce", "returned mail"]
        ):
            return "bounce"
        if any(p in text for p in ["spam", "junk", "bulk"]):
            return "spam"
        if any(
            p in text
            for p in ["entrevista", "interview", "agendar", "schedule", "conversa"]
        ):
            return "entrevista"
        if any(
            p in text
            for p in [
                "recebemos",
                "recibemos",
                "received",
                "application received",
                "candidatura recebida",
            ]
        ):
            return "confirmacao"
        if any(
            p in text
            for p in [
                "nao seguiremos",
                "not selected",
                "other candidate",
                "seguir com outro",
                "agradecemos",
            ]
        ):
            return "rejeicao"
        if any(p in text for p in ["teste", "challenge", "desafio", "technical test"]):
            return "teste_tecnico"

        return "resposta"

    async def classificar_email(self, email_data: dict) -> dict:
        tipo = self._detectar_tipo(
            email_data.get("assunto", ""),
            email_data.get("de_email", ""),
            email_data.get("corpo", ""),
        )
        vaga_id = self._extrair_vaga_id(
            email_data.get("assunto", ""),
            email_data.get("corpo", ""),
        )

        return {
            "tipo": tipo,
            "vaga_id_candidato": vaga_id,
            "confianca": "alta" if vaga_id else "baixa",
        }

    async def sincronizar(self, db) -> list[dict]:
        if not self.configured:
            logger.warning("email_manager.sincronizar.sem_config")
            return []

        emails = await self.buscar_emails(criterio="UNSEEN", max_emails=30)
        logger.info("email_manager.sincronizar.encontrados", quantidade=len(emails))

        pipeline_col = db["pipeline"]
        vagas_col = db["vagas"]
        importados = []

        for email_data in emails:
            # Check if already imported
            existente = await db["emails_recebidos"].find_one(
                {"assunto": email_data["assunto"], "de_email": email_data["de_email"]}
            )
            if existente:
                continue

            classificacao = await self.classificar_email(email_data)

            pipeline_match = None
            vaga_titulo = None

            if classificacao["vaga_id_candidato"]:
                pipeline_match = await pipeline_col.find_one(
                    {"vaga_id": classificacao["vaga_id_candidato"]}
                )
                if pipeline_match:
                    vaga_doc = await vagas_col.find_one(
                        {
                            "_id": __import__("bson").ObjectId(
                                classificacao["vaga_id_candidato"]
                            )
                        }
                    )
                    vaga_titulo = vaga_doc.get("titulo") if vaga_doc else None

            if not pipeline_match:
                subject_lower = email_data.get("assunto", "").lower()
                empresa_lower = email_data.get("de_email", "").lower()
                cursor = pipeline_col.find({})
                async for pl in cursor:
                    vaga_doc = await vagas_col.find_one({"_id": pl["vaga_id"]})
                    if not vaga_doc:
                        continue
                    vaga_tit = vaga_doc.get("titulo", "").lower()
                    empresa = vaga_doc.get("empresa", "").lower()
                    if vaga_tit and vaga_tit in subject_lower:
                        pipeline_match = pl
                        vaga_titulo = vaga_doc.get("titulo")
                        break
                    if empresa and (
                        empresa in subject_lower or empresa in empresa_lower
                    ):
                        pipeline_match = pl
                        vaga_titulo = vaga_doc.get("titulo")
                        break

            doc = {
                "assunto": email_data["assunto"],
                "de": email_data["de"],
                "de_email": email_data["de_email"],
                "data_recebida": email_data.get("data_recebida"),
                "corpo_preview": email_data["corpo"][:500],
                "tipo": classificacao["tipo"],
                "vaga_id": str(pipeline_match["vaga_id"]) if pipeline_match else None,
                "vaga_titulo": vaga_titulo,
                "pipeline_id": str(pipeline_match["_id"]) if pipeline_match else None,
                "created_at": datetime.now(timezone.utc),
                "lida": False,
            }

            await db["emails_recebidos"].insert_one(doc)

            if pipeline_match and classificacao["tipo"] in (
                "entrevista",
                "confirmacao",
                "teste_tecnico",
            ):
                await pipeline_col.update_one(
                    {"_id": pipeline_match["_id"]},
                    {
                        "$set": {
                            "email_resposta_recebida": True,
                            "email_resposta_tipo": classificacao["tipo"],
                        }
                    },
                )
                logger.info(
                    "email_manager.pipeline_atualizado",
                    pipeline_id=str(pipeline_match["_id"]),
                    tipo=classificacao["tipo"],
                )

            importados.append(doc)

        return importados

    async def enviar_email(
        self,
        para: str,
        assunto: str,
        corpo_html: str,
        corpo_texto: Optional[str] = None,
    ) -> bool:
        if (
            not settings.email_smtp_host
            or not settings.email_user
            or not settings.email_pass
        ):
            logger.warning("email_manager.enviar.sem_config")
            return False

        try:
            msg = MIMEMultipart("alternative")
            msg["From"] = settings.email_from or settings.email_user
            msg["To"] = para
            msg["Subject"] = assunto

            if corpo_texto:
                msg.attach(MIMEText(corpo_texto, "plain"))
            msg.attach(MIMEText(corpo_html, "html"))

            def _send():
                with smtplib.SMTP(
                    settings.email_smtp_host, settings.email_smtp_port or 587
                ) as server:
                    server.starttls()
                    server.login(settings.email_user, settings.email_pass)
                    server.send_message(msg)

            await asyncio.to_thread(_send)
            logger.info("email_manager.enviado", para=para, assunto=assunto)
            return True

        except Exception as e:
            logger.error("email_manager.enviar.erro", para=para, error=str(e))
            return False


email_manager = EmailManager()
