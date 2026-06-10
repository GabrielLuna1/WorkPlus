from typing import Optional, List
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorDatabase
from bson.objectid import ObjectId
from core.database import database
from core.logger import logger
from models.evento import EventoDB, EventoResponse, EventoCreate

router = APIRouter()

USER_ID = "default"


async def get_db() -> AsyncIOMotorDatabase:
    ok = await database.ensure_connected()
    if not ok:
        raise HTTPException(status_code=503, detail="Banco de dados indisponivel")
    return database.get_db()


def _utc(dt) -> Optional[datetime]:
    if dt is None or isinstance(dt, str):
        return dt
    if isinstance(dt, datetime) and dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _format(doc: dict) -> EventoResponse:
    return EventoResponse(
        id=str(doc["_id"]),
        pipeline_id=str(doc["pipeline_id"]) if doc.get("pipeline_id") else None,
        vaga_id=doc["vaga_id"],
        empresa=doc.get("empresa", ""),
        titulo=doc.get("titulo", ""),
        tipo=doc.get("tipo", ""),
        data_inicio=_utc(doc.get("data_inicio", datetime.utcnow())),
        data_fim=_utc(doc.get("data_fim")),
        descricao=doc.get("descricao", ""),
        local=doc.get("local", ""),
        url=doc.get("url", ""),
        status=doc.get("status", "pendente"),
        created_at=_utc(doc["created_at"]),
        updated_at=_utc(doc["updated_at"]),
    )


@router.post("/", response_model=EventoResponse)
async def criar_evento(
    body: EventoCreate,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = body.model_dump()
    doc["user_id"] = USER_ID
    doc["created_at"] = datetime.utcnow()
    doc["updated_at"] = datetime.utcnow()
    result = await db["eventos"].insert_one(doc)
    created = await db["eventos"].find_one({"_id": result.inserted_id})
    return _format(created)


@router.get("/", response_model=List[EventoResponse])
async def listar_eventos(
    de: Optional[datetime] = Query(None),
    ate: Optional[datetime] = Query(None),
    pipeline_id: Optional[str] = None,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    filtro: dict = {"user_id": USER_ID}
    if de or ate:
        filtro["data_inicio"] = {}
        if de:
            filtro["data_inicio"]["$gte"] = de
        if ate:
            filtro["data_inicio"]["$lte"] = ate
    if pipeline_id:
        filtro["pipeline_id"] = pipeline_id

    docs = await db["eventos"].find(filtro).sort("data_inicio", 1).to_list(length=200)
    return [_format(d) for d in docs]


@router.get("/{evento_id}", response_model=EventoResponse)
async def obter_evento(
    evento_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    doc = await db["eventos"].find_one({"_id": ObjectId(evento_id), "user_id": USER_ID})
    if not doc:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    return _format(doc)


@router.patch("/{evento_id}", response_model=EventoResponse)
async def atualizar_evento(
    evento_id: str,
    body: dict,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    campos = {"data_inicio", "data_fim", "descricao", "local", "status", "tipo"}
    update = {k: v for k, v in body.items() if k in campos}
    if not update:
        raise HTTPException(status_code=400, detail="Nenhum campo valido")
    update["updated_at"] = datetime.utcnow()
    await db["eventos"].update_one(
        {"_id": ObjectId(evento_id), "user_id": USER_ID},
        {"$set": update},
    )
    doc = await db["eventos"].find_one({"_id": ObjectId(evento_id)})
    return _format(doc)


@router.delete("/{evento_id}")
async def deletar_evento(
    evento_id: str,
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    result = await db["eventos"].delete_one(
        {"_id": ObjectId(evento_id), "user_id": USER_ID}
    )
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Evento nao encontrado")
    return {"ok": True}


@router.post("/cleanup-orphans")
async def limpar_eventos_orfaos(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Remove eventos de calendÃ¡rio cujo pipeline_id nÃ£o existe mais."""
    eventos = (
        await db["eventos"]
        .find(
            {
                "user_id": USER_ID,
                "pipeline_id": {"$ne": None},
            }
        )
        .to_list(length=200)
    )

    removidos = 0
    for ev in eventos:
        pipe = (
            await db["pipeline"].find_one({"_id": ObjectId(ev["pipeline_id"])})
            if ObjectId.is_valid(ev["pipeline_id"])
            else None
        )
        if not pipe:
            await db["eventos"].delete_one({"_id": ev["_id"]})
            removidos += 1

    logger.info("eventos.cleanup", removidos=removidos)
    return {"removidos": removidos}


@router.post("/sync-pipeline", response_model=List[EventoResponse])
async def sincronizar_pipeline(
    db: AsyncIOMotorDatabase = Depends(get_db),
):
    """Cria/atualiza eventos para itens do pipeline que tem proxima_data."""
    pipe_items = (
        await db["pipeline"]
        .find(
            {
                "user_id": USER_ID,
                "proxima_data": {"$ne": None},
            }
        )
        .to_list(length=100)
    )

    criados = []
    for item in pipe_items:
        if not item.get("proxima_data"):
            continue

        etapa = item.get("etapa", "")
        mapping = {
            "entrevista_rh": "entrevista_rh",
            "entrevista_tecnica": "entrevista_tecnica",
            "teste_tecnico": "teste_tecnico",
        }
        tipo = mapping.get(etapa, "follow_up")

        existing = await db["eventos"].find_one(
            {
                "pipeline_id": str(item["_id"]),
                "user_id": USER_ID,
            }
        )

        if existing:
            data_inicio = (
                EventoCreate(data_inicio=item["proxima_data"]).data_inicio
                if item.get("proxima_data")
                else None
            )
            await db["eventos"].update_one(
                {"_id": existing["_id"]},
                {
                    "$set": {
                        "data_inicio": data_inicio,
                        "titulo": item.get("vaga_titulo", ""),
                        "empresa": item.get("empresa", ""),
                        "descricao": item.get("proxima_acao", ""),
                        "tipo": tipo,
                        "updated_at": datetime.utcnow(),
                    }
                },
            )
            doc = await db["eventos"].find_one({"_id": existing["_id"]})
            criados.append(_format(doc))
        else:
            novo_evento = EventoCreate(
                pipeline_id=str(item["_id"]),
                vaga_id=item.get("vaga_id", ""),
                empresa=item.get("empresa", ""),
                titulo=item.get("vaga_titulo", ""),
                tipo=tipo,
                data_inicio=item["proxima_data"],
                descricao=item.get("proxima_acao", ""),
                url=item.get("url", ""),
            )
            doc_dict = novo_evento.model_dump()
            doc_dict["user_id"] = USER_ID
            doc_dict["created_at"] = datetime.utcnow()
            doc_dict["updated_at"] = datetime.utcnow()
            result = await db["eventos"].insert_one(doc_dict)
            doc = await db["eventos"].find_one({"_id": result.inserted_id})
            criados.append(_format(doc))

    return criados
