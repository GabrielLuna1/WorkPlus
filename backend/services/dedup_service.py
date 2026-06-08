import hashlib
from typing import Dict, List, Set
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import BulkWriteError
from models.vaga import VagaBruta, VagaDB


def calcular_hash(vaga: VagaBruta) -> str:
    raw = f"{vaga.fonte}:{vaga.id_externo}:{vaga.titulo}:{vaga.empresa}"
    return hashlib.sha256(raw.encode()).hexdigest()


class DedupService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db

    async def filtrar_novas(self, vagas: List[VagaBruta]) -> List[VagaDB]:
        if not vagas:
            return []

        hash_map: Dict[str, VagaBruta] = {}
        for v in vagas:
            h = calcular_hash(v)
            hash_map[h] = v

        existentes = (
            await self.db["vagas"]
            .find(
                {"hash": {"$in": list(hash_map.keys())}},
                {"hash": 1},
            )
            .to_list(length=len(hash_map))
        )
        existentes_set: Set[str] = {d["hash"] for d in existentes}

        novas: List[VagaDB] = []
        for h, v in hash_map.items():
            if h not in existentes_set:
                novas.append(VagaDB(**v.model_dump(), hash=h))
        return novas

    async def inserir_lote(self, vagas: List[VagaDB]) -> int:
        if not vagas:
            return 0
        dicts = [v.model_dump() for v in vagas]
        try:
            result = await self.db["vagas"].insert_many(dicts, ordered=False)
            return len(result.inserted_ids)
        except BulkWriteError as e:
            return e.details.get("nInserted", 0)
