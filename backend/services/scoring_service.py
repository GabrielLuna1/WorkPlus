import re
from typing import List, Optional
from motor.motor_asyncio import AsyncIOMotorDatabase
from models.vaga import VagaBruta, VagaDB
from models.perfil_usuario import PerfilUsuario, StackItem


# Vagas tech FORA do escopo (Full Stack cobre front + back, então backend é aceito)
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

# Palavras que identificam vaga como Front-End ou Full Stack
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

# Áreas que devem receber penalidade severa
AREAS_IRRELEVANTES = [
    "marketing",
    "vendas",
    "comercial",
    "financeiro",
    "administrativo",
    "rh",
    "recursos humanos",
    "contabilidade",
    "jurídico",
    "direito",
    "logística",
    "atendimento",
    "telemarketing",
    "auxiliar",
    "recepcionista",
    "secretária",
    "operador de caixa",
    "motorista",
    "porteiro",
    "zelador",
    "vendedor",
    "promotor de vendas",
    "comprador",
    "almoxarife",
    "farmacêutico",
    "nutricionista",
]


class ScoringService:
    def __init__(self, db: AsyncIOMotorDatabase) -> None:
        self.db = db
        self._perfil_cache: Optional[PerfilUsuario] = None
        self._categorias_cache: Optional[list] = None

    async def calcular(self, vaga: VagaBruta | VagaDB) -> int:
        perfil = await self._carregar_perfil()
        if not perfil:
            return 50

        score = 0
        titulo_lower = vaga.titulo.lower()
        descricao_lower = vaga.descricao.lower() if vaga.descricao else ""
        texto = f"{titulo_lower} {descricao_lower}"

        # 1. Relevância do cargo (0-25 pontos)
        score += self._score_cargo(titulo_lower, perfil.cargos_alvo)

        # 2. Match de skills (0-40 pontos)
        score += self._score_skills(texto, perfil.stacks_atuais, 40)
        score += self._score_skills(texto, perfil.stacks_aprendendo, 10)

        # 3. Localização (0-15 pontos)
        score += self._score_localizacao(
            vaga.localizacao, perfil.preferencias_localizacao
        )

        # 4. Bônus de área foco (0-10 pontos)
        score += self._score_area_foco(texto, perfil.area_foco)

        # 4.5. Modelo de Trabalho (0-20 pontos)
        score += self._score_modelo_trabalho(
            getattr(vaga, "modelo_trabalho", "nao_informado"),
            getattr(perfil, "modelos_trabalho", []),
        )

        # 4.6. Bônus de categoria (score_bonus das categorias dinâmicas)
        score += await self._score_categorias(texto)

        # 4.7. Bônus/penalidade foco Front-End / Full Stack (-40 a +30)
        score += self._score_foco_frontend(titulo_lower, texto)

        # 5. Penalidade: área irrelevante (-50)
        score += self._penalidade_area_irrelevante(titulo_lower, texto)

        # 6. Penalidade: palavras a evitar (-20 cada)
        score += self._score_evitar(texto, perfil.palavras_chave_evitar)

        return max(0, min(100, score))

    def _score_cargo(self, titulo: str, cargos_alvo: Optional[List[str]]) -> int:
        """Verifica se o título da vaga corresponde a um cargo-alvo do perfil."""
        if not cargos_alvo:
            return 10  # Sem preferência → pontuação neutra

        melhor_match = 0
        for cargo in cargos_alvo:
            cargo_lower = cargo.lower()
            # Match exato no título
            if cargo_lower in titulo:
                return 25
            # Match parcial (palavras do cargo no título)
            palavras_cargo = cargo_lower.split()
            encontradas = sum(1 for p in palavras_cargo if p in titulo)
            if len(palavras_cargo) > 0:
                ratio = encontradas / len(palavras_cargo)
                pontos = int(ratio * 20)
                melhor_match = max(melhor_match, pontos)

        return melhor_match

    def _score_skills(
        self, texto: str, stacks: Optional[List[StackItem]], max_pontos: int
    ) -> int:
        """Calcula pontuação baseado em quantas skills do perfil aparecem na vaga."""
        if not stacks:
            return 0

        encontradas = 0
        for s in stacks:
            nome_lower = s.nome.lower()
            # Busca com word boundary para evitar falsos positivos
            if re.search(r"\b" + re.escape(nome_lower) + r"\b", texto):
                encontradas += 1
            # Variações comuns
            elif nome_lower == "next.js" and ("nextjs" in texto or "next js" in texto):
                encontradas += 1
            elif nome_lower == "node.js" and ("nodejs" in texto or "node js" in texto):
                encontradas += 1
            elif nome_lower == "tailwind css" and (
                "tailwindcss" in texto or "tailwind" in texto
            ):
                encontradas += 1

        if encontradas == 0:
            return 0

        # Escala proporcional mas com diminishing returns
        ratio = min(encontradas / max(len(stacks), 1), 1.0)
        return min(max_pontos, int(ratio * max_pontos * 1.5))

    def _score_localizacao(
        self, local: Optional[str], preferencias: Optional[List[str]]
    ) -> int:
        """Pontua vagas que mencionam localização preferida ou remoto."""
        if not local or not preferencias:
            return 5

        local_lower = local.lower()
        for p in preferencias:
            if p.lower() in local_lower:
                return 15
        return 3

    def _score_area_foco(self, texto: str, areas: Optional[List[str]]) -> int:
        """Bônus se a vaga é da área foco do usuário."""
        if not areas:
            return 0

        area_keywords = {
            "frontend": [
                "frontend",
                "front-end",
                "front end",
                "react",
                "vue",
                "angular",
                "css",
                "html",
                "ui",
            ],
            "backend": [
                "backend",
                "back-end",
                "back end",
                "api",
                "server",
                "microserviço",
                "banco de dados",
            ],
            "fullstack": ["full stack", "fullstack", "full-stack"],
            "ia": [
                "machine learning",
                "deep learning",
                "nlp",
                "ia",
                "inteligência artificial",
                "llm",
                "gpt",
                "ml",
            ],
            "desenvolvimento": [
                "desenvolvedor",
                "developer",
                "programador",
                "software",
                "engenheiro",
            ],
            "devops": [
                "devops",
                "sre",
                "infraestrutura",
                "cloud",
                "kubernetes",
                "docker",
                "ci/cd",
            ],
        }

        pontos = 0
        for area in areas:
            keywords = area_keywords.get(area.lower(), [])
            for kw in keywords:
                if kw in texto:
                    pontos += 3
                    break  # Máximo 3 por área

        return min(10, pontos)

    def _score_modelo_trabalho(self, modelo: str, preferencias: List[str]) -> int:
        """Pontua baseado no modelo de trabalho preferido. O usuário quer prioritariamente remoto."""
        if not preferencias or modelo == "nao_informado":
            return 0

        preferencias_lower = [p.lower() for p in preferencias]
        if modelo == "remoto" and "remoto" in preferencias_lower:
            return 20
        elif modelo == "hibrido" and "hibrido" in preferencias_lower:
            return 10
        elif modelo == "hibrido" and "remoto" in preferencias_lower:
            return 5  # Híbrido ganha um pouco se o foco é remoto
        return 0

    async def _score_categorias(self, texto: str) -> int:
        if self._categorias_cache is not None:
            categorias = self._categorias_cache
        else:
            try:
                categorias = (
                    await self.db["categorias_vaga"]
                    .find({"ativa": True})
                    .to_list(length=None)
                )
                self._categorias_cache = categorias
            except Exception:
                return 0
        bonus = 0
        for cat in categorias:
            keywords = cat.get("keywords_include", [])
            if not keywords:
                continue
            for kw in keywords:
                if kw.lower() in texto:
                    bonus += cat.get("score_bonus", 0)
                    break
        return max(-100, min(100, bonus))

    def _penalidade_area_irrelevante(self, titulo: str, texto_completo: str) -> int:
        """Penaliza severamente vagas que são claramente fora de tech."""
        for area in AREAS_IRRELEVANTES:
            if area in titulo:
                # Verificar se tem algo de tech para não penalizar falsos positivos
                tech_signals = [
                    "desenvolvedor",
                    "developer",
                    "software",
                    "programador",
                    "react",
                    "python",
                    "java",
                    "node",
                    "frontend",
                    "backend",
                ]
                if any(ts in texto_completo for ts in tech_signals):
                    return 0  # Falso positivo — não penalizar
                return -50
        return 0

    def _score_evitar(self, texto: str, evitar: Optional[List[str]]) -> int:
        """Penaliza vagas que contêm palavras que o usuário quer evitar."""
        if not evitar:
            return 0
        penalidade = 0
        for p in evitar:
            if p.lower() in texto:
                penalidade -= 20
        return penalidade

    def _score_foco_frontend(self, titulo: str, texto_completo: str) -> int:
        """
        Bônus para vagas Front-End / Full Stack.
        Penalidade severa para vagas tech que NÃO são Front-End nem Full Stack.
        """
        # Penalidade para techs fora do escopo (mobile, data, devops, etc.)
        # Full Stack cobre front + back, então backend não é penalizado
        for kw in OUTRAS_TECHS_FORA_ESCOPO:
            if kw in titulo:
                # Proteção: se o texto completo menciona frontend/fullstack
                texto_lower = texto_completo.lower()
                for prot in FRONTEND_FULLSTACK_KEYWORDS:
                    if prot in texto_lower:
                        return 0
                return -40

        # Bônus se o título indica Front-End ou Full Stack
        for kw in FRONTEND_FULLSTACK_KEYWORDS:
            if kw in titulo:
                return 30

        return 0

    async def _carregar_perfil(self) -> Optional[PerfilUsuario]:
        if self._perfil_cache is not None:
            return self._perfil_cache

        doc = await self.db["perfil_usuario"].find_one({})
        if not doc:
            doc = {}

        # Prefer profile extraído automaticamente para stacks/cargos
        profile = await self.db["profiles"].find_one({})
        if profile:
            stack_principal = profile.get("stack_principal", [])
            if stack_principal and not doc.get("stacks_atuais"):
                doc["stacks_atuais"] = [
                    {"nome": s, "nivel": "intermediario"}
                    for s in stack_principal
                    if isinstance(s, str)
                ]
            titulo = profile.get("titulo_profissional", "")
            if titulo and not doc.get("cargos_alvo"):
                doc["cargos_alvo"] = [titulo]
            if not doc.get("cidade"):
                doc["cidade"] = profile.get("cidade", "")

        curriculo = await self.db["curriculo_versoes"].find_one(
            {"ativo": True}, sort=[("versao", -1)]
        )
        if curriculo:
            estruturado = curriculo.get("estruturado") or curriculo
            skills = estruturado.get("skills", [])

            if skills:
                doc["stacks_atuais"] = [
                    {"nome": s, "nivel": "intermediario"}
                    for s in skills
                    if isinstance(s, str)
                ]

            if not doc.get("cargos_alvo"):
                cargos = []
                for exp in estruturado.get("experiencias", []):
                    cargo = exp.get("cargo")
                    if cargo and cargo not in cargos:
                        cargos.append(cargo)
                doc["cargos_alvo"] = cargos[:3]

        if not doc and not curriculo:
            return None

        for campo in [
            "cargos_alvo",
            "area_foco",
            "palavras_chave_busca",
            "stacks_atuais",
            "stacks_aprendendo",
            "experiencias",
            "educacao",
            "certificados",
            "projetos",
            "preferencias_localizacao",
            "modelos_trabalho",
            "palavras_chave_evitar",
        ]:
            if campo in doc and doc[campo] is None:
                doc[campo] = [] if campo != "area_foco" else ["desenvolvimento"]
                if campo == "modelos_trabalho":
                    doc[campo] = ["remoto"]
        try:
            self._perfil_cache = PerfilUsuario(**doc)
            return self._perfil_cache
        except Exception:
            return None
