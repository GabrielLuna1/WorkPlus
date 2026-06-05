import json
import re
from typing import Optional

from core.logger import logger
from ai.client import _call_with_retry


async def analisar_match(
    curriculo: dict,
    vaga: dict,
) -> Optional[dict]:
    """
    Analisa a compatibilidade entre currículo e vaga.
    Retorna insights, sugestões e gaps — NUNCA modifica o currículo.
    """
    skills_cv = ", ".join(curriculo.get("skills", []))
    experiencias_texto = _formatar_experiencias(curriculo.get("experiencias", []))
    formacoes_texto = _formatar_formacoes(curriculo.get("formacoes", []))

    prompt = (
        "Você é um analista de currículos especializado em tecnologia. "
        "Sua função é ANALISAR a compatibilidade entre um currículo e uma vaga, "
        "sem modificar ou reescrever nenhuma informação do candidato.\n\n"
        "REGRAS:\n"
        "1. NÃO reescreva o currículo. NÃO modifique nenhum dado.\n"
        "2. NÃO invente skills ou experiências que o candidato não tem.\n"
        "3. Seja honesto sobre gaps e pontos fracos.\n"
        "4. Sugira melhorias que o usuário pode fazer MANUALMENTE.\n"
        "5. Destaque skills da vaga que estão faltando no currículo.\n\n"
        "=== VAGA ===\n"
        f"Título: {vaga.get('titulo', '')}\n"
        f"Empresa: {vaga.get('empresa', '')}\n"
        f"Descrição: {vaga.get('descricao', '')[:3000]}\n\n"
        "=== CURRÍCULO ===\n"
        f"Nome: {curriculo.get('nome', '')}\n"
        f"Resumo: {curriculo.get('resumo_profissional', '')}\n"
        f"Skills: {skills_cv}\n\n"
        f"Experiências:\n{experiencias_texto}\n\n"
        f"Formação:\n{formacoes_texto}\n\n"
        "Retorne APENAS um JSON válido com estes campos:\n"
        "{\n"
        '  "compatibilidade_geral": "ALTA | MÉDIA | BAIXA",\n'
        '  "score_estimado": 0-100 (número inteiro),\n'
        '  "pontos_fortes": ["lista de pontos fortes do match"],\n'
        '  "pontos_fracos": ["lista de pontos fracos ou gaps"],\n'
        '  "skills_presentes": ["skills da vaga que o candidato tem"],\n'
        '  "skills_faltando": ["skills da vaga que faltam no currículo"],\n'
        '  "sugestoes": ["sugestões acionáveis para o candidato melhorar o match"],\n'
        '  "observacao_geral": "resumo da análise em 1-2 frases"\n'
        "}"
    )

    try:
        content = await _call_with_retry(
            [{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=2048,
            timeout=120,
        )
        if not content:
            logger.warning("resume_analyzer.sem_resposta")
            return None
        return _parse_json(content)
    except Exception as e:
        logger.warning("resume_analyzer.erro", error=str(e))
        return None


def _formatar_experiencias(experiencias: list) -> str:
    linhas = []
    for e in experiencias:
        empresa = e.get("empresa", "?")
        cargo = e.get("cargo", "?")
        desc = e.get("descricao", [])
        if isinstance(desc, list):
            desc = "; ".join(desc)
        linhas.append(f"- {cargo} na {empresa}: {desc}")
    return "\n".join(linhas)


def _formatar_formacoes(formacoes: list) -> str:
    linhas = []
    for f in formacoes:
        curso = f.get("curso", "?")
        inst = f.get("instituicao", "?")
        linhas.append(f"- {curso} — {inst}")
    return "\n".join(linhas)


def _parse_json(content: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", content, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None
