import re
from dataclasses import dataclass, field
from datetime import datetime
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional

import pdfplumber
import docx2txt

from models.curriculo_model import (
    CurriculoSchema,
    ExperienciaProfissional,
    Projeto,
    Formacao,
    Certificacao,
    Idioma,
    SecaoGenerica,
)


SKILL_NORMALIZATION_MAP = {
    "node": "Node.js",
    "node.js": "Node.js",
    "nodejs": "Node.js",
    "next": "Next.js",
    "next.js": "Next.js",
    "nextjs": "Next.js",
    "react": "React",
    "react.js": "React",
    "reactjs": "React",
    "typescript": "TypeScript",
    "ts": "TypeScript",
    "javascript": "JavaScript",
    "js": "JavaScript",
    "tailwind": "Tailwind CSS",
    "tailwindcss": "Tailwind CSS",
    "mongodb": "MongoDB",
    "mongo": "MongoDB",
    "postgresql": "PostgreSQL",
    "postgres": "PostgreSQL",
    "sql server": "SQL Server",
    "sqlserver": "SQL Server",
    "fastapi": "FastAPI",
    "docker": "Docker",
    "kubernetes": "Kubernetes",
    "k8s": "Kubernetes",
    "aws": "AWS",
    "gcp": "GCP",
    "azure": "Azure",
    "graphql": "GraphQL",
    "html": "HTML5",
    "html5": "HTML5",
    "css": "CSS3",
    "css3": "CSS3",
    "git": "Git",
    "github": "GitHub",
}

KNOWN_SKILLS = {
    "python",
    "java",
    "c#",
    "c++",
    "csharp",
    "ruby",
    "php",
    "go",
    "golang",
    "rust",
    "swift",
    "kotlin",
    "scala",
    "elixir",
    "dart",
    "flutter",
    "react",
    "next.js",
    "nextjs",
    "vue",
    "vue.js",
    "angular",
    "svelte",
    "node.js",
    "nodejs",
    "express",
    "nestjs",
    "django",
    "flask",
    "fastapi",
    "spring boot",
    "spring",
    "laravel",
    "rails",
    "asp.net",
    "typescript",
    "javascript",
    "jquery",
    "tailwind css",
    "bootstrap",
    "sass",
    "html5",
    "css3",
    "webpack",
    "vite",
    "babel",
    "eslint",
    "postgresql",
    "postgres",
    "mysql",
    "mongodb",
    "mongo",
    "redis",
    "sqlite",
    "oracle",
    "sql server",
    "mariadb",
    "firebase",
    "supabase",
    "docker",
    "kubernetes",
    "k8s",
    "terraform",
    "ansible",
    "jenkins",
    "github actions",
    "gitlab ci",
    "circleci",
    "aws",
    "gcp",
    "azure",
    "linux",
    "bash",
    "powershell",
    "nginx",
    "apache",
    "graphql",
    "rest",
    "grpc",
    "websocket",
    "rabbitmq",
    "kafka",
    "machine learning",
    "deep learning",
    "tensorflow",
    "pytorch",
    "scikit-learn",
    "pandas",
    "numpy",
    "jupyter",
    "nlp",
    "llm",
    "openai",
    "langchain",
    "git",
    "github",
    "gitlab",
    "bitbucket",
    "jira",
    "confluence",
    "figma",
    "adobe xd",
    "photoshop",
    "illustrator",
    "unity",
    "unreal engine",
    "blender",
}


# --- Regex patterns ---

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}")
PHONE_RE = re.compile(r"(?:\+?\d{1,3}[\s.-]?)?\(?\d{2,3}\)?[\s.-]?\d{4,5}[\s.-]?\d{4}")
LINKEDIN_RE = re.compile(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9_-]+/?")
GITHUB_RE = re.compile(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9_-]+/?")
URL_RE = re.compile(
    r"(?:https?://)?(?:[a-zA-Z0-9-]+\.)+(?:com|org|net|io|dev|app|gov|edu|br|com\.br)(?:\/[^\s()]*)?(?=\s|$|\)|\.)"
)
DATE_RANGE_RE = re.compile(
    r"((?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4})\s*(?:[-–—a]+)\s*((?:jan|fev|mar|abr|mai|jun|jul|ago|set|out|nov|dez|january|february|march|april|may|june|july|august|september|october|november|december|jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*\.?\s*\d{4}|atual|presente?|o momento|currently)",
    re.IGNORECASE,
)


# --- Data structures ---


@dataclass
class BlockClassification:
    type: str
    confidence: float
    raw: str
    alternatives: list[tuple[str, float]] = field(default_factory=list)


@dataclass
class ParsingReport:
    total_blocks: int = 0
    classified_blocks: int = 0
    custom_blocks: int = 0
    avg_confidence: float = 0.0
    warnings: list[str] = field(default_factory=list)
    blocks: list[BlockClassification] = field(default_factory=list)


# --- Universal section definitions ---

# (type, pt_titles, en_titles, es_titles, keywords, abbreviations)
SECTION_DEFINITIONS = [
    (
        "experience",
        [
            "experiência profissional",
            "experiência",
            "experiências profissionais",
            "histórico profissional",
            "trajetória profissional",
            "carreira",
        ],
        [
            "work experience",
            "professional experience",
            "professional background",
            "career history",
            "employment history",
            "work history",
            "relevant experience",
            "professional history",
            "professional journey",
            "work background",
            "job experience",
            "work timeline",
        ],
        [
            "experiencia profesional",
            "trayectoria profesional",
            "carrera",
            "historial laboral",
            "antecedentes profesionales",
        ],
        [
            "empresa",
            "company",
            "cargo",
            "position",
            "role",
            "responsável",
            "responsible",
            "reportava",
        ],
        ["exp.", "prof. exp.", "work exp.", "carreira"],
    ),
    (
        "education",
        [
            "formação acadêmica",
            "educação",
            "formação",
            "escolaridade",
        ],
        [
            "education",
            "academic background",
            "academic formation",
            "educational background",
            "academic qualifications",
            "formal education",
            "academic history",
        ],
        [
            "formación académica",
            "educación",
            "formación",
        ],
        [
            "universidade",
            "university",
            "college",
            "faculdade",
            "bacharel",
            "bachelor",
            "mestrado",
            "master",
            "doutorado",
            "phd",
            "licenciatura",
            "graduação",
            "graduate",
        ],
        ["acad.", "formação", "educ.", "schooling"],
    ),
    (
        "skills",
        [
            "habilidades",
            "competências técnicas",
            "competências",
            "conhecimentos",
            "principais habilidades",
            "tecnologias",
            "stack",
            "ferramentas",
        ],
        [
            "skills",
            "technical skills",
            "core competencies",
            "technologies",
            "tools",
            "tech stack",
            "expertise",
            "technical expertise",
            "key skills",
            "professional skills",
            "tools & technologies",
            "technical proficiencies",
        ],
        [
            "habilidades",
            "competencias técnicas",
            "competencias",
            "conocimientos",
            "tecnologías",
            "herramientas",
        ],
        [
            "react",
            "python",
            "javascript",
            "aws",
            "docker",
            "node",
            "typescript",
            "html",
            "css",
        ],
        ["tech stack", "skills", "tools", "comp.", "tec."],
    ),
    (
        "projects",
        [
            "projetos",
            "projetos de engenharia",
            "portfólio",
            "projetos realizados",
        ],
        [
            "projects",
            "portfolio",
            "personal projects",
            "key projects",
            "featured projects",
            "project portfolio",
            "professional projects",
            "side projects",
        ],
        [
            "proyectos",
            "portafolio",
            "proyectos realizados",
        ],
        [
            "github",
            "repositório",
            "repository",
            "deploy",
            "aplicação",
            "application",
            "app",
        ],
        ["proj.", "portfolio", "cases"],
    ),
    (
        "certifications",
        [
            "certificações",
            "cursos",
            "certificados",
            "certificações & aperfeiçoamento",
        ],
        [
            "certifications",
            "courses",
            "certificates",
            "licenses",
            "licenses & certifications",
            "certification & training",
            "professional development",
            "training",
        ],
        [
            "certificaciones",
            "cursos",
            "certificados",
        ],
        [
            "certified",
            "certificação",
            "bootcamp",
            "udemy",
            "coursera",
            "origamid",
            "alura",
            "rocketseat",
        ],
        ["certs", "cert.", "licenses", "training"],
    ),
    (
        "languages",
        [
            "idiomas",
            "línguas",
        ],
        [
            "languages",
            "language proficiency",
            "language skills",
        ],
        [
            "idiomas",
            "lenguas",
        ],
        [
            "fluente",
            "fluent",
            "nativo",
            "native",
            "inglês",
            "english",
            "português",
            "portuguese",
            "espanhol",
            "spanish",
            "intermediário",
            "intermediate",
            "básico",
            "basic",
        ],
        ["lang.", "idiomas"],
    ),
    (
        "summary",
        [
            "resumo profissional",
            "objetivo",
            "perfil profissional",
            "sobre",
        ],
        [
            "summary",
            "professional summary",
            "profile",
            "about me",
            "career objective",
            "personal statement",
            "professional profile",
            "qualifications summary",
            "executive summary",
        ],
        [
            "resumen profesional",
            "perfil profesional",
            "sobre mí",
        ],
        [],
        ["summary", "profile", "about", "resumo", "objetivo"],
    ),
]

# Whitelist for custom sections that should never be discarded
CUSTOM_SECTION_WHITELIST = [
    "open source",
    "open-source",
    "volunteering",
    "volunteer",
    "achievements",
    "publications",
    "hackathons",
    "research",
    "awards",
    "honors",
    "patents",
    "leadership",
    "extracurricular",
    "interests",
    "conferences",
    "speaking",
    "community",
]

SOCIAL_PROVIDERS = {
    "linkedin.com": "linkedin",
    "github.com": "github",
    "gitlab.com": "gitlab",
    "behance.net": "behance",
    "dribbble.com": "dribbble",
    "medium.com": "medium",
    "dev.to": "devto",
    "stackoverflow.com": "stackoverflow",
    "vercel.app": "portfolio",
    "netlify.app": "portfolio",
}


# --- Utility functions ---


def _normalize_for_matching(text: str) -> str:
    text = text.lower().strip().rstrip(":").strip()
    text = re.sub(r"\s*\(.*?\)\s*", "", text).strip()
    text = re.sub(r"\s*&.*$", "", text).strip()
    text = text.replace("-", " ").replace("–", " ").replace("—", " ")
    text = re.sub(r"[^a-z0-9áéíóúãõâêôçàüñ\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _fuzzy_match(text: str, candidates: list[str]) -> float:
    norm = _normalize_for_matching(text)
    if not norm:
        return 0.0
    best = 0.0
    for c in candidates:
        ratio = SequenceMatcher(None, norm, _normalize_for_matching(c)).ratio()
        if ratio > best:
            best = ratio
    return best


def _structural_hints(section_type: str, text: str) -> float:
    text_lower = text.lower()
    score = 0.0
    if section_type == "experience":
        if DATE_RANGE_RE.search(text):
            score += 0.5
        if any(
            kw in text_lower
            for kw in ["empresa", "company", "cargo", "position", "role"]
        ):
            score += 0.3
        if len(text.split("\n")) >= 3:
            score += 0.2
    elif section_type == "education":
        if any(
            kw in text_lower
            for kw in ["universidade", "university", "college", "faculdade"]
        ):
            score += 0.5
        if any(
            kw in text_lower
            for kw in [
                "bacharel",
                "bachelor",
                "mestrado",
                "master",
                "phd",
                "doutorado",
                "tecnólogo",
            ]
        ):
            score += 0.3
        if re.search(r"\b(19\d{2}|20\d{2})\b", text):
            score += 0.2
    elif section_type == "skills":
        known_hits = sum(
            1
            for s in KNOWN_SKILLS
            if re.search(r"\b" + re.escape(s) + r"\b", text_lower)
        )
        score = min(known_hits * 0.15, 0.8)
    elif section_type == "projects":
        if any(
            kw in text_lower for kw in ["github", "git", "repositório", "repository"]
        ):
            score += 0.4
        if URL_RE.search(text):
            score += 0.3
        if any(
            kw in text_lower for kw in ["app", "platform", "sistema", "system", "api"]
        ):
            score += 0.2
    elif section_type == "certifications":
        if any(
            kw in text_lower
            for kw in ["certified", "bootcamp", "udemy", "coursera", "origamid"]
        ):
            score += 0.5
        if re.search(r"\b(19\d{2}|20\d{2})\b", text):
            score += 0.2
    elif section_type == "languages":
        if any(
            kw in text_lower
            for kw in ["fluente", "fluent", "nativo", "native", "inglês", "english"]
        ):
            score += 0.5
    elif section_type == "summary":
        lines = text.strip().split("\n")
        if 1 <= len(lines) <= 5 and sum(len(l) for l in lines) < 600:
            score += 0.4
        if not DATE_RANGE_RE.search(text):
            score += 0.3
        if not any(
            kw in text_lower
            for kw in ["empresa", "company", "universidade", "university"]
        ):
            score += 0.2
    return min(score, 1.0)


def _negative_signals(section_type: str, text: str) -> float:
    text_lower = text.lower()
    penalty = 0.0
    if section_type == "skills":
        if DATE_RANGE_RE.search(text):
            penalty += 0.5
        if any(kw in text_lower for kw in ["empresa", "company", "cargo"]):
            penalty += 0.3
    elif section_type == "experience":
        lines = [l for l in text.split("\n") if l.strip()]
        if len(lines) < 2:
            penalty += 0.4
        if not DATE_RANGE_RE.search(text) and not any(
            kw in text_lower for kw in ["empresa", "company"]
        ):
            penalty += 0.3
    elif section_type == "education":
        if not re.search(r"\b(19\d{2}|20\d{2})\b", text):
            penalty += 0.2
        if not any(
            kw in text_lower
            for kw in ["universidade", "university", "college", "faculdade", "curso"]
        ):
            penalty += 0.3
    return min(penalty, 1.0)


def _detect_dominant_language(blocks: list[str]) -> str:
    en_score = 0
    pt_score = 0
    es_score = 0
    for _, en_titles, *_ in SECTION_DEFINITIONS:
        pass
    for text in blocks:
        tl = text.lower()
        for _, pt_titles, en_titles, es_titles, _, _ in SECTION_DEFINITIONS:
            for t in pt_titles:
                if t in tl:
                    pt_score += 1
            for t in en_titles:
                if t in tl:
                    en_score += 1
            for t in es_titles:
                if t in tl:
                    es_score += 1
    if en_score >= pt_score and en_score >= es_score:
        return "en"
    if pt_score >= es_score:
        return "pt"
    return "es"


def _classify_block(text: str, dominant_lang: str = "pt") -> BlockClassification:
    lines = text.strip().split("\n")
    first_line = lines[0].strip().lower() if lines else ""
    body = "\n".join(lines[1:]) if len(lines) > 1 else ""

    best = BlockClassification(type="unknown", confidence=0.0, raw=text)
    alternatives: list[tuple[str, float]] = []

    for (
        tipo,
        pt_titles,
        en_titles,
        es_titles,
        keywords,
        abbreviations,
    ) in SECTION_DEFINITIONS:
        # 1. Fuzzy match with headings (weight 50%)
        title_lists = [pt_titles]
        if dominant_lang == "en":
            title_lists = [en_titles, pt_titles]
        elif dominant_lang == "es":
            title_lists = [es_titles, pt_titles]
        else:
            title_lists = [pt_titles, en_titles]
        title_lists.append(abbreviations)

        head_score = 0.0
        for tlist in title_lists:
            head_score = max(head_score, _fuzzy_match(first_line, tlist))

        # 2. Keyword match in BODY only (weight 20%)
        if keywords and body:
            body_lower = body.lower()
            kw_hits = sum(1 for kw in keywords if kw in body_lower)
            kw_score = min(kw_hits / max(len(keywords), 1) * 3, 1.0)
        else:
            kw_score = 0.0

        # 3. Structural hints from BODY only (weight 20%)
        struct_score = _structural_hints(tipo, body) if body else 0.0

        # 4. Negative signals from full text (weight 10%)
        neg_score = _negative_signals(tipo, text)

        raw_confidence = (
            head_score * 0.5 + kw_score * 0.2 + struct_score * 0.2 - neg_score * 0.1
        )
        head_floor = head_score * 0.7
        confidence = min(max(max(raw_confidence, head_floor), 0.0), 1.0)
        alternatives.append((tipo, round(confidence, 4)))

        if confidence > best.confidence:
            best = BlockClassification(
                type=tipo,
                confidence=round(confidence, 4),
                raw=text,
            )

    best.alternatives = sorted(alternatives, key=lambda x: x[1], reverse=True)[:3]
    return best


# --- Extraction functions ---


def extract_text_from_pdf(file_path: str) -> str:
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text.strip()


def extract_links_from_pdf(file_path: str) -> list[dict]:
    links = []
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            annots = page.annots
            if not annots:
                continue
            for a in annots:
                uri = a.get("uri", "")
                if not uri:
                    continue
                links.append({"uri": uri, "page": a.get("page", 0)})
    return links


def extract_text_from_docx(file_path: str) -> str:
    return docx2txt.process(file_path) or ""


def extract_text(file_path: str) -> str:
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_path)
    elif ext in (".docx", ".doc"):
        return extract_text_from_docx(file_path)
    raise ValueError(f"Formato não suportado: {ext}")


def normalize_skills(raw_skills: list[str]) -> list[str]:
    normalized = set()
    for skill in raw_skills:
        key = skill.strip().lower()
        canonical = SKILL_NORMALIZATION_MAP.get(key, skill.strip())
        normalized.add(canonical)
    return sorted(normalized)


def _extract_list(text: str) -> list[str]:
    items = []
    for line in text.split("\n"):
        line = line.strip().lstrip("•-*●◦‣⁃–—").strip()
        if line and len(line) > 2:
            items.append(line)
    return items


def _find_first_line_containing(text: str, *patterns: re.Pattern) -> Optional[str]:
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        for pat in patterns:
            match = pat.search(line)
            if match:
                return line
    return None


def _split_blocks(text: str) -> list[str]:
    blocks = re.split(r"\n\s*\n", text)
    return [b.strip() for b in blocks if b.strip()]


def _is_likely_section(text: str) -> bool:
    first_line = text.strip().split("\n")[0].strip()
    if not first_line:
        return False
    if len(first_line) < 3 or len(first_line) > 60:
        return False
    if (
        EMAIL_RE.match(first_line)
        or LINKEDIN_RE.match(first_line)
        or GITHUB_RE.match(first_line)
    ):
        return False
    if "@" in first_line or "http" in first_line.lower():
        return False
    if re.search(r"\b(19\d{2}|20\d{2})\b", first_line):
        return False
    return True


def _detect_header_region(
    raw_text: str, classified_blocks: list[BlockClassification]
) -> str:
    first_section_idx = len(raw_text)
    for block in classified_blocks:
        if (
            block.type != "unknown"
            and block.confidence >= 0.50
            and _is_likely_section(block.raw)
        ):
            pos = raw_text.find(block.raw[:50])
            if 0 < pos < first_section_idx:
                first_section_idx = pos
    return (
        raw_text[:first_section_idx].strip()
        if first_section_idx < len(raw_text)
        else ""
    )


def _extract_header_contextual(raw_text: str, file_path: str) -> dict:
    lines = raw_text.split("\n")
    pdf_links: list[dict] = []
    ext = Path(file_path).suffix.lower()
    if ext == ".pdf":
        try:
            pdf_links = extract_links_from_pdf(file_path)
        except Exception:
            pdf_links = []

    uri_set: set[str] = {l["uri"] for l in pdf_links}
    mailto_set: set[str] = {
        u.replace("mailto:", "") for u in uri_set if u.startswith("mailto:")
    }
    http_links: list[str] = [u for u in uri_set if u.startswith("http")]

    # Email — global regex + annotation priority
    email: Optional[str] = None
    if mailto_set:
        email = next(iter(mailto_set))
    if not email:
        email_match = EMAIL_RE.search(raw_text)
        email = email_match.group(0) if email_match else None

    # Phone — global regex
    phone_match = PHONE_RE.search(raw_text)
    telefone = phone_match.group(0).strip() if phone_match else None

    # LinkedIn — annotation priority
    linkedin: Optional[str] = None
    for url in http_links:
        if "linkedin.com" in url.lower():
            linkedin = url
            break
    if not linkedin:
        linkedin_match = LINKEDIN_RE.search(raw_text)
        linkedin = linkedin_match.group(0) if linkedin_match else None
        if linkedin and not linkedin.startswith("http"):
            linkedin = f"https://{linkedin}"

    # GitHub — annotation priority
    github: Optional[str] = None
    for url in http_links:
        if "github.com" in url.lower() and "/" in url.replace("github.com", "").strip(
            "/"
        ):
            github = url
            break
    if not github:
        github_match = GITHUB_RE.search(raw_text)
        github = github_match.group(0) if github_match else None
        if github and not github.startswith("http"):
            github = f"https://{github}"

    # Portfolio — annotation priority (restante que não é linkedin/github/email)
    portfolio: Optional[str] = None
    for url in http_links:
        lower = url.lower()
        if "linkedin" in lower or "github" in lower or "mailto:" in url:
            continue
        portfolio = url
        break
    if not portfolio:
        url_matches = URL_RE.findall(raw_text)
        for url in url_matches:
            full_url = url[0] if isinstance(url, tuple) else url
            lower = full_url.lower()
            if "linkedin" in lower or "github" in lower:
                continue
            if re.search(r"@" + re.escape(full_url.split("/")[0]), raw_text):
                continue
            portfolio = (
                full_url if full_url.startswith("http") else f"https://{full_url}"
            )
            break

    # Social provider auto-detection
    social: dict[str, str] = {}
    for url in http_links:
        for domain, provider in SOCIAL_PROVIDERS.items():
            if domain in url.lower():
                if provider not in social:
                    social[provider] = url
                break

    # Name — first contextual block (not email/phone/URL, 2-5 words, capitalized)
    nome = ""
    for line in lines[:20]:
        stripped = line.strip()
        if not stripped:
            continue
        words = stripped.split()
        if len(words) < 2 or len(words) > 5:
            continue
        if (
            EMAIL_RE.match(stripped)
            or LINKEDIN_RE.match(stripped)
            or GITHUB_RE.match(stripped)
        ):
            continue
        if (
            any(c.isdigit() for c in stripped if c.isascii())
            and len([c for c in stripped if c.isdigit()]) > 3
        ):
            continue
        if re.search(r"\d{4}", stripped):
            continue
        if stripped.lower().startswith(
            ("curriculo", "currículo", "cv", "resume", "linkedin", "github")
        ):
            continue
        nome = stripped
        break
    if not nome:
        nome = "Currículo sem nome"

    # City — line with geographic indicators, stripping non-city tokens
    cidade = ""
    for line in lines[:20]:
        # Skip lines that look like date ranges (any year-year pattern)
        if re.search(r"\d{4}\s*[-–—]\s*\d{4}", line) or DATE_RANGE_RE.search(line):
            continue
        line_lower = line.strip().lower()
        if any(
            indicator in line_lower
            for indicator in [
                " - ",
                "brasil",
                ", sp",
                ", rj",
                ", mg",
                ", ba",
                ", rs",
                ", pr",
                "cidade:",
                "localização:",
                "localizacao:",
                "city:",
                "location:",
            ]
        ):
            city_match = re.search(
                r"([A-ZÀ-Ú][a-zà-ú]+(?:\s[A-ZÀ-Ú][a-zà-ú]+)?)\s*[-–—,]\s*([A-Z]{2})",
                line.strip(),
            )
            if city_match:
                cidade = city_match.group(1).strip()
            else:
                cleaned = line.strip()
                for prefix in [
                    "Cidade:",
                    "Localização:",
                    "Localizacao:",
                    "City:",
                    "Location:",
                ]:
                    cleaned = cleaned.replace(prefix, "").strip()
                email_suffix = re.search(r"\s*[|•]\s*" + EMAIL_RE.pattern, cleaned)
                if email_suffix:
                    cleaned = cleaned[: email_suffix.start()].strip()
                phone_s = PHONE_RE.search(cleaned)
                if phone_s:
                    cleaned = cleaned.replace(phone_s.group(0), "").strip()
                url_s = re.search(r"\s*(?:https?://)?\S+\.\w{2,}(?:/\S*)?", cleaned)
                if url_s:
                    cleaned = cleaned[: url_s.start()].strip()
                cleaned = cleaned.rstrip("|•, ").strip()
                if cleaned and len(cleaned) < 60:
                    cidade = cleaned
            break

    return {
        "nome": nome,
        "email": email or "",
        "telefone": telefone or "",
        "cidade": cidade,
        "linkedin": social.get("linkedin", linkedin or ""),
        "github": social.get("github", github or ""),
        "portfolio": social.get("portfolio", portfolio or ""),
    }


# --- Section-specific parsers ---


def _parse_experiences(section_text: str) -> list[ExperienciaProfissional]:
    experiencias: list[ExperienciaProfissional] = []
    blocks = _split_blocks(section_text)
    for block in blocks:
        if not block:
            continue
        block_lines = block.split("\n")
        header = block_lines[0].strip().lstrip("•-*●◦‣⁃–—").strip()
        cargo = ""
        empresa = ""
        data_inicio = None
        data_fim = None
        descricao: list[str] = []
        tecs: list[str] = []

        date_match = DATE_RANGE_RE.search(header)
        header_no_date = header
        if date_match:
            data_inicio = date_match.group(1).strip()
            data_fim = date_match.group(2).strip()
            header_no_date = header.replace(date_match.group(0), "").strip()
        pipe_split = header_no_date.split("|", maxsplit=1)
        if len(pipe_split) > 1:
            cargo = pipe_split[0].strip().lstrip("•-*●◦‣⁃–—").strip()
            empresa = pipe_split[1].strip().lstrip("•-*●◦‣⁃–—").strip()
        else:
            empresa = header_no_date

        for line in block_lines[1:]:
            line = line.strip()
            if not line:
                continue
            sub_date_match = DATE_RANGE_RE.search(line)
            if sub_date_match:
                if not data_inicio:
                    data_inicio = sub_date_match.group(1).strip()
                    data_fim = sub_date_match.group(2).strip()
                if not cargo:
                    cargo = (
                        line.replace(sub_date_match.group(0), "")
                        .strip()
                        .lstrip("•-*●◦‣⁃–—")
                        .strip()
                    )
            elif not cargo:
                cargo = line.lstrip("•-*●◦‣⁃–—").strip()
            else:
                cleaned = line.lstrip("•-*●◦‣⁃–—").strip()
                if cleaned:
                    descricao.append(cleaned)
                    for skill in KNOWN_SKILLS:
                        if re.search(r"\b" + re.escape(skill) + r"\b", cleaned.lower()):
                            formatted = SKILL_NORMALIZATION_MAP.get(
                                skill, skill.title()
                            )
                            if formatted not in tecs:
                                tecs.append(formatted)

        experiencias.append(
            ExperienciaProfissional(
                empresa=empresa,
                cargo=cargo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                descricao=descricao,
                tecnologias=tecs,
            )
        )
    return experiencias


def _parse_education(section_text: str) -> list[Formacao]:
    formacoes: list[Formacao] = []
    blocks = _split_blocks(section_text)
    for block in blocks:
        if not block:
            continue
        block_lines = block.split("\n")
        curso_line = block_lines[0].strip().lstrip("•-*●◦‣⁃–—").strip()
        instituicao = ""
        data_conclusao = None
        nivel = None

        nivel_match = re.search(
            r"\((Tecn[óo]logo|Bacharelado|Licenciatura|MBA|Mestrado|Doutorado|P[óo]s[-\s]gradua[cç][ãa]o|Especializa[cç][ãa]o|Curso\s+T[eé]cnico|Aperfei[çc]oamento)\)",
            curso_line,
            re.IGNORECASE,
        )
        if nivel_match:
            nivel = nivel_match.group(1)
            curso_line = (
                curso_line[: nivel_match.start()] + curso_line[nivel_match.end() :]
            ).strip()
        date_match_curso = re.search(
            r"(?:Conclu[íi]do\s+(?:em\s+)?)?((?:Jan|Fev|Mar|Abr|Mai|Jun|Jul|Ago|Set|Out|Nov|Dez)[a-z]*[./]\s*\d{4}|\d{4})",
            curso_line,
            re.IGNORECASE,
        )
        if date_match_curso:
            data_conclusao = date_match_curso.group(1)
            curso_line = (
                curso_line[: date_match_curso.start()]
                + curso_line[date_match_curso.end() :]
            ).strip()
        curso = curso_line.strip(" -–—")

        for line in block_lines[1:]:
            line = line.strip()
            if not line:
                continue
            if not instituicao:
                instituicao = line.lstrip("•-*●◦‣⁃–—").strip()
                date_match = re.search(r"\d{4}", line)
                if date_match:
                    data_conclusao = date_match.group(0)
            else:
                date_match = re.search(r"\d{4}", line)
                if date_match:
                    data_conclusao = date_match.group(0)

        formacoes.append(
            Formacao(
                curso=curso,
                instituicao=instituicao,
                nivel=nivel,
                data_conclusao=data_conclusao,
                em_andamento=False,
            )
        )
    return formacoes


def _parse_certifications(section_text: str) -> list[Certificacao]:
    certificacoes: list[Certificacao] = []
    raw_lines = section_text.split("\n")
    CERT_INSTITUTIONS = [
        "onebitcode",
        "origamid",
        "impacta",
        "faculdade impacta",
        "alura",
        "rocketseat",
        "udemy",
        "coursera",
        "edx",
        "fia",
        "fiap",
        "senai",
        "senac",
        "fgv",
    ]

    def _is_cert_title(line: str) -> bool:
        lowered = line.lower()
        if any(inst in lowered for inst in CERT_INSTITUTIONS):
            return True
        if re.search(
            r"\((?:Bootcamp|Curso|Certif|Treinamento|Programa)", line, re.IGNORECASE
        ):
            return True
        if lowered.startswith(("programador", "especializa")):
            return True
        return False

    cert_buffer: Optional[dict] = None
    for line in raw_lines:
        stripped = line.strip().lstrip("•-*●◦‣⁃–—").strip()
        if not stripped:
            continue
        if not _is_cert_title(stripped) and cert_buffer is not None:
            cert_buffer["descricao"] = stripped
            continue
        if cert_buffer is not None:
            nome_cert = cert_buffer["nome"]
            instituicao_cert = cert_buffer.get("instituicao")
            ano = cert_buffer.get("ano")
            cert_descricao = cert_buffer.get("descricao")
            ano_match = re.search(r"\b(19\d{2}|20\d{2})\b", nome_cert)
            if ano_match and not ano:
                ano = ano_match.group(0)
                nome_cert = nome_cert.replace(ano_match.group(0), "").strip(" -–—")
            sep_match = re.search(r"[-–—]\s+", nome_cert)
            if sep_match:
                partes = re.split(r"\s*[-–—]\s+", nome_cert, maxsplit=1)
                nome_cert = partes[0].strip()
                if not instituicao_cert:
                    instituicao_cert = partes[1].strip() if len(partes) > 1 else None
            INST_LIST = sorted(CERT_INSTITUTIONS, key=len, reverse=True)
            for inst in INST_LIST:
                if inst.lower() in nome_cert.lower():
                    idx = nome_cert.lower().index(inst.lower())
                    if idx > 0:
                        instituicao_cert = nome_cert[idx:].strip(" -–—)")
                        nome_cert = nome_cert[:idx].strip(" -–—.,")
                    else:
                        instituicao_cert = inst
                    break
            certificacoes.append(
                Certificacao(
                    nome=nome_cert,
                    instituicao=instituicao_cert,
                    ano=ano,
                    descricao=cert_descricao,
                )
            )
        cert_buffer = {
            "nome": stripped,
            "ano": None,
            "instituicao": None,
            "descricao": None,
        }
        ano_match = re.search(r"\b(19\d{2}|20\d{2})\b", stripped)
        if ano_match:
            cert_buffer["ano"] = ano_match.group(0)

    if cert_buffer is not None:
        nome_cert = cert_buffer["nome"]
        instituicao_cert = cert_buffer.get("instituicao")
        ano = cert_buffer.get("ano")
        cert_descricao = cert_buffer.get("descricao")
        ano_match = re.search(r"\b(19\d{2}|20\d{2})\b", nome_cert)
        if ano_match and not ano:
            ano = ano_match.group(0)
            nome_cert = nome_cert.replace(ano_match.group(0), "").strip(" -–—")
        INST_LIST = sorted(CERT_INSTITUTIONS, key=len, reverse=True)
        for inst in INST_LIST:
            if inst.lower() in nome_cert.lower():
                idx = nome_cert.lower().index(inst.lower())
                if idx > 0:
                    instituicao_cert = nome_cert[idx:].strip(" -–—)")
                    nome_cert = nome_cert[:idx].strip(" -–—.,")
                else:
                    instituicao_cert = inst
                break
        certificacoes.append(
            Certificacao(
                nome=nome_cert,
                instituicao=instituicao_cert,
                ano=ano,
                descricao=cert_descricao,
            )
        )
    return certificacoes


def _parse_projects(section_text: str) -> list[Projeto]:
    projetos: list[Projeto] = []
    lines = section_text.split("\n")
    project_blocks: list[list[str]] = []
    current_block: list[str] = []
    PROJ_TITLE_RE = re.compile(
        r"^[A-Za-z\u00c0-\u024f\ufffd][A-Za-z\u00c0-\u024f\ufffd\-\s]+(?:V\d|Pro|Enterprise|System|Platform|Engine|API|App|Profissional)[\.\s]*(?:\(.*\))?\s*$"
    )
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if current_block:
                project_blocks.append(current_block)
                current_block = []
            continue
        if current_block and PROJ_TITLE_RE.match(stripped) and len(stripped) < 80:
            project_blocks.append(current_block)
            current_block = [stripped]
        else:
            current_block.append(stripped)
    if current_block:
        project_blocks.append(current_block)

    for block_lines in project_blocks:
        if not block_lines:
            continue
        nome_proj = block_lines[0].strip().lstrip("•-*●◦‣⁃–—").strip()
        desc_proj = None
        bullets_proj: list[str] = []
        tec_proj: list[str] = []
        url_proj = None

        for line in block_lines[1:]:
            line = line.strip()
            if not line:
                continue
            url_match = URL_RE.search(line)
            if url_match:
                raw = url_match.group(0).rstrip(")")
                url_proj = raw if raw.startswith("http") else f"https://{raw}"
            cleaned = line.lstrip("•-*●◦‣⁃–—").strip()
            if cleaned:
                if not desc_proj:
                    desc_proj = cleaned
                else:
                    bullets_proj.append(cleaned)
                for skill in KNOWN_SKILLS:
                    if re.search(r"\b" + re.escape(skill) + r"\b", cleaned.lower()):
                        formatted = SKILL_NORMALIZATION_MAP.get(skill, skill.title())
                        if formatted not in tec_proj:
                            tec_proj.append(formatted)

        projetos.append(
            Projeto(
                nome=nome_proj,
                descricao=desc_proj,
                bullets=bullets_proj,
                tecnologias=tec_proj,
                url=url_proj,
            )
        )
    return projetos


# --- Main parse function ---


async def parse_resume(file_path: str) -> CurriculoSchema:
    # ETAPA 1: Extração bruta
    raw_text = extract_text(file_path)
    if not raw_text or len(raw_text) < 50:
        raise ValueError("Não foi possível extrair texto do arquivo.")

    # ETAPA 2: Normalização (unicode, whitespace)
    normalized_text = raw_text.strip()
    normalized_text = re.sub(r"\r\n", "\n", normalized_text)
    normalized_text = re.sub(r"[ \t]+", " ", normalized_text)

    # ETAPA 3: Classificação fuzzy dos blocos
    raw_blocks = _split_blocks(normalized_text)
    dominant_lang = _detect_dominant_language(raw_blocks)

    classified_blocks: list[BlockClassification] = []
    for block in raw_blocks:
        cls = _classify_block(block, dominant_lang)
        classified_blocks.append(cls)

    # ETAPA 3.5: Encontrar posição da primeira seção (fim do header)
    first_section_idx = len(normalized_text)
    for block in classified_blocks:
        if (
            block.type != "unknown"
            and block.confidence >= 0.50
            and _is_likely_section(block.raw)
        ):
            pos = normalized_text.find(block.raw[:50])
            if 0 < pos < first_section_idx:
                first_section_idx = pos

    # ETAPA 4: Estruturação
    header_data = _extract_header_contextual(raw_text, file_path)

    # Agrupar blocos classificados por tipo (pulando blocos do header)
    blocks_by_type: dict[str, list[str]] = {}
    report = ParsingReport(total_blocks=len(classified_blocks))
    for cls in classified_blocks:
        # Skip blocks entirely within header region
        block_start = normalized_text.find(cls.raw[:50]) if cls.raw else -1
        if 0 <= block_start < first_section_idx:
            continue

        if cls.confidence >= 0.45:
            t = cls.type
            # Strip section title line from block content for parsing
            lines = cls.raw.split("\n")
            body = "\n".join(lines[1:]).strip() if len(lines) > 1 else ""
            block_content = body if body else cls.raw
        else:
            t = "custom"
            report.custom_blocks += 1
            block_content = cls.raw
        blocks_by_type.setdefault(t, []).append(block_content)
        report.blocks.append(cls)

    report.classified_blocks = len(classified_blocks) - report.custom_blocks
    if classified_blocks:
        report.avg_confidence = round(
            sum(c.confidence for c in classified_blocks) / len(classified_blocks), 4
        )

    # Skills: from section + inline detection
    raw_skills: list[str] = []
    for block_text in blocks_by_type.get("skills", []):
        raw_skills.extend(_extract_list(block_text))

    text_lower = normalized_text.lower()
    for skill in KNOWN_SKILLS:
        if skill not in [s.lower() for s in raw_skills]:
            if re.search(r"\b" + re.escape(skill) + r"\b", text_lower):
                formatted = SKILL_NORMALIZATION_MAP.get(skill, skill.title())
                if formatted not in raw_skills:
                    raw_skills.append(formatted)

    skills = normalize_skills(raw_skills)

    # Experiences
    experiencias: list[ExperienciaProfissional] = []
    for block_text in blocks_by_type.get("experience", []):
        experiencias.extend(_parse_experiences(block_text))

    # Education
    formacoes: list[Formacao] = []
    for block_text in blocks_by_type.get("education", []):
        formacoes.extend(_parse_education(block_text))

    # Certifications
    certificacoes: list[Certificacao] = []
    for block_text in blocks_by_type.get("certifications", []):
        certificacoes.extend(_parse_certifications(block_text))

    # Projects
    projetos: list[Projeto] = []
    for block_text in blocks_by_type.get("projects", []):
        projetos.extend(_parse_projects(block_text))

    # Languages
    idiomas: list[Idioma] = []
    for block_text in blocks_by_type.get("languages", []):
        items = _extract_list(block_text)
        for item in items:
            idioma_parts = re.split(r"[-–—:]\s*", item, maxsplit=1)
            idioma_nome = idioma_parts[0].strip()
            nivel = (
                idioma_parts[1].strip() if len(idioma_parts) > 1 else "Não informado"
            )
            idiomas.append(Idioma(idioma=idioma_nome, nivel=nivel))

    # Summary
    resumo_profissional = None
    for block_text in blocks_by_type.get("summary", []):
        resumo_profissional = block_text.strip()
        break

    # Custom sections (unknown + whitelisted)
    secoes_personalizadas: list[SecaoGenerica] = []
    seen_custom: set[str] = set()
    for cls in classified_blocks:
        if cls.confidence >= 0.45 and cls.type not in ("custom",):
            continue
        first_line = cls.raw.split("\n")[0].strip().lower()
        is_whitelisted = any(ws in first_line for ws in CUSTOM_SECTION_WHITELIST)
        if not is_whitelisted and cls.confidence >= 0.45:
            continue
        titulo = cls.raw.split("\n")[0].strip().rstrip(":").strip()
        if titulo.lower() in seen_custom:
            continue
        seen_custom.add(titulo.lower())
        conteudo = "\n".join(cls.raw.split("\n")[1:]).strip()
        if conteudo:
            secoes_personalizadas.append(
                SecaoGenerica(
                    titulo=titulo, conteudo=conteudo, ordem=len(secoes_personalizadas)
                )
            )

    curriculo = CurriculoSchema(
        nome=header_data["nome"],
        email=header_data["email"],
        telefone=header_data["telefone"],
        cidade=header_data["cidade"],
        linkedin=header_data["linkedin"],
        portfolio=header_data["portfolio"],
        github=header_data["github"],
        resumo_profissional=resumo_profissional,
        experiencias=experiencias,
        projetos=projetos,
        formacoes=formacoes,
        certificacoes=certificacoes,
        idiomas=idiomas,
        skills=skills,
        secoes_personalizadas=secoes_personalizadas,
        fonte_arquivo=Path(file_path).suffix.lower().replace(".", ""),
        criado_em=datetime.utcnow(),
        atualizado_em=datetime.utcnow(),
        arquivo_original_path=file_path,
        # Parsing metadata
        texto_bruto=raw_text,
        idioma_detectado=dominant_lang,
        parsing_confidence=report.avg_confidence,
        parsing_warnings=report.warnings,
        total_secoes_detectadas=report.classified_blocks,
    )

    return curriculo
