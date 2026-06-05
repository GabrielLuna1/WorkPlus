import re
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vaga import VagaDB
from models.perfil_usuario import PerfilUsuario
from core.logger import logger
from services.categoria_service import CategoriaService

# Mesmas listas do scoring_service — vagas tech fora do escopo
# Full Stack cobre front + back, então backend é aceito
OUTRAS_TECHS_FORA_ESCOPO = [
    "analista de dados",
    "cientista de dados",
    "data engineer",
    "data analyst",
    "engenheiro de dados",
    "data science",
    "devops",
    "sre",
    "infraestrutura",
    "cloud engineer",
    "sysadmin",
    "segurança",
    "security analyst",
    "pentest",
    "blue team",
    "red team",
    "mobile",
    "android",
    "ios",
    "flutter",
    "react native",
    "kotlin",
    "qa",
    "quality assurance",
    "teste",
    "test automation",
    "suporte técnico",
    "suporte ti",
    "help desk",
    "analista de suporte",
    "dba",
    "administrador de banco de dados",
    "banco de dados",
    "wordpress developer",
    "wordpress",
    "joomla",
    "sap",
    "oracle",
    "salesforce",
    "dynamics",
    "mainframe",
    "cobol",
    "delphi",
    "visual basic",
    "estágio em ti",
    "estágio ti",
]

FRONTEND_FULLSTACK_KEYWORDS = [
    "front-end",
    "frontend",
    "front end",
    "full stack",
    "fullstack",
    "full-stack",
    "react",
    "next.js",
    "nextjs",
    "vue",
    "vue.js",
    "angular",
    "ui developer",
    "ui engineer",
    "front end developer",
    "desenvolvedor front",
    "desenvolvedor full",
]


class RelevanceFilter:
    def __init__(self, db: Optional[AsyncIOMotorDatabase] = None):
        self._cat_svc = CategoriaService(db) if db is not None else None

    async def filtrar(
        self,
        vagas: List[VagaDB],
        perfil: Optional[PerfilUsuario] = None,
    ) -> tuple[List[VagaDB], int]:
        aprovadas: List[VagaDB] = []
        removidas = 0

        categorias = []
        if self._cat_svc is not None:
            categorias = await self._cat_svc.get_ativas()

        tech_keywords = []
        va_keywords = []
        irrelevant_keywords = []

        for cat in categorias:
            if cat.id == "tech":
                tech_keywords = [k.lower() for k in cat.keywords_include]
            elif cat.id == "va":
                va_keywords = [k.lower() for k in cat.keywords_include]
            elif cat.id == "irrelevant":
                irrelevant_keywords = [k.lower() for k in cat.keywords_include]

        evitar_perfil: List[str] = []
        if perfil and perfil.palavras_chave_evitar:
            evitar_perfil = [p.lower() for p in perfil.palavras_chave_evitar]

        for vaga in vagas:
            motivo = self._checar(
                vaga, tech_keywords, va_keywords, irrelevant_keywords, evitar_perfil
            )
            if motivo:
                logger.debug(
                    "relevance_filter.removida",
                    titulo=vaga.titulo[:60],
                    motivo=motivo,
                )
                removidas += 1
            else:
                aprovadas.append(vaga)

        if removidas > 0:
            logger.info(
                "relevance_filter.resultado",
                total_entrada=len(vagas),
                aprovadas=len(aprovadas),
                removidas=removidas,
            )

        return aprovadas, removidas

    def _checar(
        self,
        vaga: VagaDB,
        tech_keywords: List[str],
        va_keywords: List[str],
        irrelevant_keywords: List[str],
        evitar_perfil: List[str],
    ) -> Optional[str]:
        titulo_lower = vaga.titulo.lower()
        descricao_lower = vaga.descricao.lower() if vaga.descricao else ""
        texto = f"{titulo_lower} {descricao_lower}"

        if not vaga.descricao or len(vaga.descricao.strip()) < 50:
            return "sem_descricao"

        tem_sinal_tech = (
            any(k in texto for k in tech_keywords) if tech_keywords else False
        )
        tem_sinal_va = any(k in texto for k in va_keywords) if va_keywords else False
        protegido = tem_sinal_tech or tem_sinal_va

        # CHECK 1: Rejeitar vagas tech fora do foco (backend, mobile, data, etc.)
        # a menos que o título também mencione frontend/fullstack
        for kw in OUTRAS_TECHS_FORA_ESCOPO:
            if kw in titulo_lower:
                if any(fk in texto for fk in FRONTEND_FULLSTACK_KEYWORDS):
                    return None  # Protegido: menciona frontend/fullstack
                return f"fora_do_foco:{kw}"

        # CHECK 2: Desativado para evitar falsos negativos em vagas de título genérico
        # (ex: "Desenvolvedor de Sistemas" ou "Software Engineer") que usam React/Node na descrição.
        # tem_front = any(fk in titulo_lower for fk in FRONTEND_FULLSTACK_KEYWORDS)
        # if not tem_front and not tem_sinal_tech and not tem_sinal_va:
        #     return "sem_sinal_frontend"

        for palavra in irrelevant_keywords:
            if palavra in titulo_lower:
                if protegido:
                    return None
                return f"irrelevante:{palavra}"

        for palavra in evitar_perfil:
            if palavra in titulo_lower:
                if protegido:
                    return None
                return f"palavra_evitar:{palavra}"

        return None


async def limpar_vagas_irrelevantes(db) -> dict:
    pipeline_docs = await db["pipeline"].find({}, {"vaga_id": 1}).to_list(length=10000)
    pipeline_vaga_ids = {doc["vaga_id"] for doc in pipeline_docs}

    filtro = RelevanceFilter(db)
    categorias = []
    if filtro._cat_svc is not None:
        categorias = await filtro._cat_svc.get_ativas()

    tech_keywords = []
    irrelevant_keywords = []
    for cat in categorias:
        if cat.id == "tech":
            tech_keywords = [k.lower() for k in cat.keywords_include]
        elif cat.id == "irrelevant":
            irrelevant_keywords = [k.lower() for k in cat.keywords_include]

    total_antes = await db["vagas"].count_documents({})

    filtro_remover = {
        "$or": [
            {"descricao": {"$in": [None, "", " "]}},
            {"$expr": {"$lt": [{"$strLenCP": {"$ifNull": ["$descricao", ""]}}, 50]}},
            {"score": {"$lt": 10}},
        ]
    }

    candidatas = (
        await db["vagas"]
        .find(filtro_remover, {"_id": 1, "titulo": 1, "descricao": 1})
        .to_list(length=10000)
    )

    ids_remover: set = set()
    for doc in candidatas:
        vid = str(doc["_id"])
        if vid not in pipeline_vaga_ids:
            ids_remover.add(doc["_id"])

    if irrelevant_keywords:
        regex_irrelevant = "|".join(re.escape(k) for k in irrelevant_keywords[:30])
        vagas_area = (
            await db["vagas"]
            .find(
                {"titulo": {"$regex": regex_irrelevant, "$options": "i"}},
                {"_id": 1, "titulo": 1, "descricao": 1},
            )
            .to_list(length=10000)
        )

        for doc in vagas_area:
            vid = str(doc["_id"])
            if vid in pipeline_vaga_ids:
                continue
            texto = f"{doc.get('titulo', '')} {doc.get('descricao', '')}".lower()
            tem_tech = any(k in texto for k in tech_keywords)
            if not tem_tech:
                ids_remover.add(doc["_id"])

    # Remove vagas tech fora do escopo (mobile, data, devops, etc.)
    for kw in OUTRAS_TECHS_FORA_ESCOPO:
        vagas_fora_foco = (
            await db["vagas"]
            .find(
                {"titulo": {"$regex": re.escape(kw), "$options": "i"}},
                {"_id": 1, "titulo": 1},
            )
            .to_list(length=5000)
        )
        for doc in vagas_fora_foco:
            vid = str(doc["_id"])
            if vid in pipeline_vaga_ids:
                continue
            titulo = doc.get("titulo", "").lower()
            # Proteção: se menciona frontend/fullstack, preserva
            if any(fk in titulo for fk in FRONTEND_FULLSTACK_KEYWORDS):
                continue
            ids_remover.add(doc["_id"])

    removidas = 0
    if ids_remover:
        result = await db["vagas"].delete_many({"_id": {"$in": list(ids_remover)}})
        removidas = result.deleted_count

    total_depois = await db["vagas"].count_documents({})

    logger.info(
        "limpar_vagas.concluido",
        total_antes=total_antes,
        removidas=removidas,
        total_depois=total_depois,
        protegidas_pipeline=len(pipeline_vaga_ids),
    )

    return {
        "total_antes": total_antes,
        "removidas": removidas,
        "total_depois": total_depois,
        "protegidas_pipeline": len(pipeline_vaga_ids),
    }
