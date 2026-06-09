import httpx
from core.config import settings
from core.logger import logger

TELEGRAM_API = "https://api.telegram.org/bot"


async def _send_message(chat_id: str, text: str, parse_mode: str = "HTML") -> bool:
    token = settings.telegram_bot_token
    if not token or not chat_id:
        return False
    try:
        url = f"{TELEGRAM_API}{token}/sendMessage"
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                url,
                json={
                    "chat_id": chat_id,
                    "text": text,
                    "parse_mode": parse_mode,
                    "disable_web_page_preview": True,
                },
            )
            if resp.status_code != 200:
                logger.warning(
                    "telegram.erro_envio", status=resp.status_code, body=resp.text
                )
            return resp.status_code == 200
    except Exception as e:
        logger.error("telegram.erro", error=str(e))
        return False


async def notificar_match(
    chat_id: str, titulo: str, empresa: str, score: int, url: str = ""
) -> bool:
    text = (
        f"<b>ðŸ”¥ Match Supremo! Score: {score}</b>\n\n"
        f"<b>{titulo}</b>\n"
        f"{'ðŸ¢ ' + empresa if empresa else ''}"
    )
    if url:
        text += f"\n\n<a href='{url}'>Ver vaga</a>"
    return await _send_message(chat_id, text)


async def notificar_pipeline(
    chat_id: str, titulo: str, empresa: str, etapa_antiga: str, etapa_nova: str
) -> bool:
    emoji = {
        "salva": "ðŸ“Œ",
        "aplicada": "ðŸ“¨",
        "em_analise": "ðŸ”",
        "entrevista_rh": "ðŸ“ž",
        "entrevista_tecnica": "ðŸ’»",
        "teste_tecnico": "ðŸ§ª",
        "contratado": "✅",
        "rejeitado": "❌",
    }.get(etapa_nova, "ðŸ”„")

    nomes = {
        "salva": "Salva",
        "aplicada": "Aplicada",
        "em_analise": "Em Análise",
        "entrevista_rh": "Entrevista RH",
        "entrevista_tecnica": "Entrevista Técnica",
        "teste_tecnico": "Teste Técnico",
        "contratado": "Contratado",
        "rejeitado": "Rejeitado",
    }

    text = (
        f"<b>{emoji} Pipeline Atualizado</b>\n\n"
        f"<b>{titulo}</b>\n"
        f"{'ðŸ¢ ' + empresa if empresa else ''}\n"
        f"{nomes.get(etapa_antiga, etapa_antiga)} → {nomes.get(etapa_nova, etapa_nova)}"
    )
    return await _send_message(chat_id, text)


async def notificar_resumo_diario(
    chat_id: str,
    novas_vagas: int,
    pipeline: dict[str, int],
    top_vagas: list[dict],
) -> bool:
    text = "<b>📊 Resumo Diário — WorkHunter</b>\n\n"
    text += f"<b>Novas vagas hoje:</b> {novas_vagas}\n\n"

    text += "<b>Pipeline:</b>\n"
    for etapa, nome in [
        ("salva", "ðŸ“Œ Salvas"),
        ("aplicada", "ðŸ“¨ Aplicadas"),
        ("em_analise", "ðŸ” Em Análise"),
        ("entrevista_rh", "ðŸ“ž Entrevista RH"),
        ("entrevista_tecnica", "ðŸ’» Entrevista Técnica"),
        ("teste_tecnico", "ðŸ§ª Teste"),
        ("contratado", "✅ Contratado"),
        ("rejeitado", "❌ Rejeitado"),
    ]:
        count = pipeline.get(etapa, 0)
        if count > 0:
            text += f"{nome}: {count}\n"

    if top_vagas:
        text += "\n<b>ðŸ”¥ Melhores matches:</b>\n"
        for v in top_vagas[:5]:
            text += f"• <b>{v.get('titulo', '?')}</b> — {v.get('empresa', '?')} (score: {v.get('score', '?')})\n"

    return await _send_message(chat_id, text)
