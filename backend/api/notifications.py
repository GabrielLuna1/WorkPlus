from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from core.database import get_db
from core.auth import get_user_id
from core.config import settings
from services.email_manager import email_manager

router = APIRouter()


@router.get("/telegram")
async def obter_config_telegram(
    user_id: str = Depends(get_user_id), db: AsyncIOMotorDatabase = Depends(get_db)
):
    doc = await db["notifications_config"].find_one({"user_id": user_id})
    config = doc or {}
    return {
        "enabled": config.get("telegram_enabled", False),
        "chat_id": config.get("telegram_chat_id") or settings.telegram_chat_id or "",
        "notify_match": config.get("telegram_notify_match", True),
        "notify_pipeline": config.get("telegram_notify_pipeline", True),
        "notify_daily": config.get("telegram_notify_daily", True),
    }


@router.put("/telegram")
async def atualizar_config_telegram(
    body: dict,
    user_id: str = Depends(get_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    update = {}
    if "enabled" in body:
        update["telegram_enabled"] = bool(body["enabled"])
    if "chat_id" in body:
        update["telegram_chat_id"] = str(body["chat_id"])
    if "notify_match" in body:
        update["telegram_notify_match"] = bool(body["notify_match"])
    if "notify_pipeline" in body:
        update["telegram_notify_pipeline"] = bool(body["notify_pipeline"])
    if "notify_daily" in body:
        update["telegram_notify_daily"] = bool(body["notify_daily"])

    if update:
        await db["notifications_config"].update_one(
            {"user_id": user_id},
            {"$set": update},
            upsert=True,
        )

    config = await db["notifications_config"].find_one({"user_id": user_id}) or {}
    return {
        "enabled": config.get("telegram_enabled", False),
        "chat_id": config.get("telegram_chat_id") or settings.telegram_chat_id or "",
        "notify_match": config.get("telegram_notify_match", True),
        "notify_pipeline": config.get("telegram_notify_pipeline", True),
        "notify_daily": config.get("telegram_notify_daily", True),
    }


@router.post("/telegram/testar")
async def testar_telegram(
    user_id: str = Depends(get_user_id),
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from services.telegram_bot import _send_message

    config = await db["notifications_config"].find_one({"user_id": user_id}) or {}
    chat_id = config.get("telegram_chat_id") or settings.telegram_chat_id
    if not chat_id:
        raise HTTPException(400, "Nenhum chat_id configurado")

    ok = await _send_message(
        chat_id, "<b>âœ… Teste</b>\n\nNotificaÃ§Ãµes do WorkHunter funcionando!"
    )
    if not ok:
        raise HTTPException(
            500, "Falha ao enviar mensagem. Verifique o token e chat_id."
        )
    return {"ok": True, "message": "Mensagem de teste enviada!"}


@router.get("/email")
async def obter_config_email():
    return {
        "configured": email_manager.configured,
        "imap_host": settings.email_imap_host or "",
        "imap_port": settings.email_imap_port or 993,
        "smtp_host": settings.email_smtp_host or "",
        "smtp_port": settings.email_smtp_port or 587,
        "email_user": settings.email_user or "",
        "email_from": settings.email_from or "",
        "check_interval_minutes": settings.email_check_interval_minutes or 15,
    }


@router.post("/email/testar")
async def testar_email():
    if not email_manager.configured:
        raise HTTPException(400, "Email nÃ£o configurado. Preencha EMAIL_* no .env")

    ok = await email_manager.connect_imap()
    if not ok:
        raise HTTPException(
            500, "Falha ao conectar via IMAP. Verifique suas credenciais."
        )

    emails = await email_manager.buscar_emails(criterio="ALL", max_emails=3)
    await email_manager.disconnect()

    return {
        "ok": True,
        "conexao_imap": ok,
        "emails_encontrados": len(emails),
        "ultimos": [
            {
                "assunto": e.get("assunto"),
                "de": e.get("de_email"),
                "data": e.get("data_recebida"),
            }
            for e in emails[:3]
        ],
    }


@router.post("/email/sync")
async def sincronizar_email(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    if not email_manager.configured:
        raise HTTPException(400, "Email nÃ£o configurado")

    importados = await email_manager.sincronizar(db)
    return {
        "ok": True,
        "importados": len(importados),
        "emails": importados,
    }


@router.get("/email/mensagens")
async def listar_emails(
    tipo: str | None = Query(None),
    lida: bool | None = Query(None),
    limit: int = 50,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filtro: dict = {}
    if tipo:
        filtro["tipo"] = tipo
    if lida is not None:
        filtro["lida"] = lida

    cursor = db["emails_recebidos"].find(filtro).sort("created_at", -1).limit(limit)
    resultados = []
    async for doc in cursor:
        doc["id"] = str(doc.pop("_id"))
        if isinstance(doc.get("created_at"), datetime):
            doc["created_at"] = doc["created_at"].isoformat()
        resultados.append(doc)
    return resultados


@router.patch("/email/{email_id}/ler")
async def marcar_como_lido(
    email_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    from bson import ObjectId

    result = await db["emails_recebidos"].update_one(
        {"_id": ObjectId(email_id)},
        {"$set": {"lida": True, "lida_em": datetime.now(timezone.utc)}},
    )
    if result.modified_count == 0:
        raise HTTPException(404, "Email nÃ£o encontrado")
    return {"ok": True}
