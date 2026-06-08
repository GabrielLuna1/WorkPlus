import json
import re
from datetime import datetime
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException
from motor.motor_asyncio import AsyncIOMotorCollection
from sse_starlette.sse import EventSourceResponse

from core.auth import get_user_id
from core.database import database
from core.logger import logger
from ai.models import ChatSessionCreate, ChatSendRequest
from ai import client as ai_client
from pydantic import BaseModel
from ai.tools import TOOL_HANDLERS

router = APIRouter()


def _sessoes() -> AsyncIOMotorCollection:
    return database.get_db()["chat_sessoes"]


def _mensagens() -> AsyncIOMotorCollection:
    return database.get_db()["chat_mensagens"]


def _db():
    return database.get_db()


def _doc_to_dict(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    for k in ("created_at", "updated_at"):
        if k in doc and isinstance(doc[k], datetime):
            doc[k] = doc[k].isoformat()
    return doc


# ─── Provider ─────────────────────────────────────────────────


class SetProviderBody(BaseModel):
    provider: str


@router.get("/provider")
async def get_provider():
    return ai_client.get_provider_info()


@router.post("/provider")
async def set_provider(body: SetProviderBody):
    try:
        ai_client.set_provider(body.provider)
        return ai_client.get_provider_info()
    except ValueError as e:
        raise HTTPException(400, str(e))


# ─── Sessions ─────────────────────────────────────────────────


@router.post("/chat/sessions")
async def criar_sessao(body: ChatSessionCreate, user_id: str = Depends(get_user_id)):
    coll = _sessoes()
    now = datetime.utcnow()
    doc = {
        "user_id": user_id,
        "titulo": body.titulo,
        "status": "active",
        "created_at": now,
        "updated_at": now,
    }
    result = await coll.insert_one(doc)
    return _doc_to_dict({"_id": result.inserted_id, **doc})


@router.get("/chat/sessions")
async def listar_sessoes(user_id: str = Depends(get_user_id)):
    coll = _sessoes()
    cursor = coll.find({"user_id": user_id}).sort("updated_at", -1).limit(50)
    return [_doc_to_dict(d) async for d in cursor]


@router.delete("/chat/sessions/{sessao_id}", status_code=204)
async def deletar_sessao(sessao_id: str, user_id: str = Depends(get_user_id)):
    coll = _sessoes()
    result = await coll.delete_one({"_id": ObjectId(sessao_id), "user_id": user_id})
    if not result.deleted_count:
        raise HTTPException(404, "Sessão não encontrada")
    await _mensagens().delete_many({"sessao_id": sessao_id})


@router.patch("/chat/sessions/{sessao_id}")
async def atualizar_sessao(
    sessao_id: str,
    body: ChatSessionCreate,
    user_id: str = Depends(get_user_id),
):
    coll = _sessoes()
    result = await coll.find_one_and_update(
        {"_id": ObjectId(sessao_id), "user_id": user_id},
        {"$set": {"titulo": body.titulo, "updated_at": datetime.utcnow()}},
    )
    if not result:
        raise HTTPException(404, "Sessão não encontrada")
    result["titulo"] = body.titulo
    return _doc_to_dict(result)


# ─── Messages ─────────────────────────────────────────────────


@router.get("/chat/sessions/{sessao_id}/messages")
async def listar_mensagens(sessao_id: str, user_id: str = Depends(get_user_id)):
    coll = _sessoes()
    sessao = await coll.find_one({"_id": ObjectId(sessao_id), "user_id": user_id})
    if not sessao:
        raise HTTPException(404, "Sessão não encontrada")
    msg_coll = _mensagens()
    cursor = msg_coll.find({"sessao_id": sessao_id}).sort("created_at", 1)
    return [_doc_to_dict(d) async for d in cursor]


# ─── Send / Stream ────────────────────────────────────────────


@router.post("/chat/sessions/{sessao_id}/send")
async def enviar_mensagem(
    sessao_id: str, body: ChatSendRequest, user_id: str = Depends(get_user_id)
):
    coll = _sessoes()
    sessao = await coll.find_one({"_id": ObjectId(sessao_id), "user_id": user_id})
    if not sessao:
        raise HTTPException(404, "Sessão não encontrada")

    msg_coll = _mensagens()
    now = datetime.utcnow()

    user_msg = {
        "sessao_id": sessao_id,
        "papel": "user",
        "conteudo": body.mensagem,
        "metadata": {"vaga_id": body.vaga_id} if body.vaga_id else None,
        "created_at": now,
    }
    await msg_coll.insert_one(user_msg)

    history = []
    cursor = msg_coll.find({"sessao_id": sessao_id}).sort("created_at", -1).limit(20)
    async for m in cursor:
        role = "assistant" if m["papel"] == "assistant" else m["papel"]
        history.append({"role": role, "content": m["conteudo"]})
    history.reverse()

    context = await _build_enriched_context(user_id, body.vaga_id)
    system = _build_system_prompt(user_id, context)
    full_messages = [{"role": "system", "content": system}] + history

    async def event_generator():
        collected = ""
        reasoning_buffer = ""
        try:
            async for event in ai_client.chat_stream(full_messages):
                if event["type"] == "reasoning":
                    reasoning_buffer += event["token"]
                    yield {
                        "data": json.dumps(
                            {"type": "reasoning", "token": event["token"]}
                        )
                    }
                elif event["type"] == "content":
                    collected += event["token"]
                    yield {
                        "data": json.dumps({"type": "content", "token": event["token"]})
                    }
        except Exception as e:
            yield {"event": "error", "data": json.dumps({"error": str(e)})}
            return

        clean_content = (
            _strip_tool_marker(collected).strip()
            if collected
            else reasoning_buffer.strip()
        )
        if not clean_content and reasoning_buffer:
            clean_content = reasoning_buffer.strip()
        tool = _detect_tool_call(collected)

        if clean_content:
            await msg_coll.insert_one(
                {
                    "sessao_id": sessao_id,
                    "papel": "assistant",
                    "conteudo": clean_content,
                    "metadata": {"tool": tool} if tool else None,
                    "created_at": datetime.utcnow(),
                }
            )

        await _sessoes().update_one(
            {"_id": ObjectId(sessao_id)},
            {"$set": {"updated_at": datetime.utcnow()}},
        )

        if tool:
            yield {"event": "tool_start", "data": json.dumps(tool)}

            db = _db()
            handler = TOOL_HANDLERS.get(tool["tool"])
            if handler:
                try:
                    tool_result = await handler(user_id, tool["params"] or "", db)
                except Exception as e:
                    logger.warning(
                        "tool.execution_error", tool=tool["tool"], error=str(e)
                    )
                    tool_result = {
                        "success": False,
                        "error": f"Erro ao executar {tool['tool']}: {str(e)}",
                    }
            else:
                tool_result = {
                    "success": False,
                    "error": f"Ferramenta '{tool['tool']}' não encontrada",
                }

            yield {"event": "tool_result", "data": json.dumps(tool_result)}

            if tool_result.get("success"):
                result_content = tool_result["result"]
                await msg_coll.insert_one(
                    {
                        "sessao_id": sessao_id,
                        "papel": "assistant",
                        "conteudo": result_content,
                        "metadata": {"tool_result": tool["tool"]},
                        "created_at": datetime.utcnow(),
                    }
                )

        yield {"event": "done", "data": "{}"}

    return EventSourceResponse(event_generator())


# ─── Enriched Context ─────────────────────────────────────────


async def _build_enriched_context(user_id: str, vaga_id: Optional[str] = None) -> dict:
    db = _db()
    context = {}

    vagas_cursor = (
        db["vagas"]
        .find(
            {},
            {
                "titulo": 1,
                "empresa": 1,
                "score": 1,
                "_id": 1,
            },
        )
        .sort("coletada_em", -1)
        .limit(5)
    )
    context["vagas_recentes"] = [
        {
            "id": str(v["_id"]),
            "titulo": v.get("titulo", ""),
            "empresa": v.get("empresa", ""),
            "score": v.get("score", 50),
        }
        async for v in vagas_cursor
    ]

    pipe_coll = db["pipeline"]
    stages = [
        "salva",
        "aplicada",
        "em_analise",
        "entrevista_rh",
        "entrevista_tecnica",
        "teste_tecnico",
        "contratado",
        "rejeitado",
    ]
    counts = {}
    for stage in stages:
        counts[stage] = await pipe_coll.count_documents(
            {"user_id": user_id, "etapa": stage}
        )
    context["pipeline_stats"] = counts
    context["pipeline_total"] = sum(counts.values())

    curriculo = await db["curriculo_versoes"].find_one(
        {"user_id": user_id, "ativo": True}, sort=[("versao", -1)]
    )
    if curriculo:
        estruturado = curriculo.get("estruturado") or curriculo

        # Extrair habilidades (skills)
        skills_raw = estruturado.get("skills") or []
        skills = [s for s in skills_raw if isinstance(s, str)]

        # Resumo das últimas 3 experiências
        exp_list = estruturado.get("experiencias") or []
        resumo_exp = []
        for e in exp_list[:3]:
            cargo = e.get("cargo", "")
            empresa = e.get("empresa", "")
            periodo = ""
            if e.get("data_inicio"):
                periodo += e.get("data_inicio")
                if e.get("data_fim"):
                    periodo += f" até {e.get('data_fim')}"

            resumo_exp.append(
                f"{cargo} na {empresa}" + (f" ({periodo})" if periodo else "")
            )

        # Raw text fallback — quando parser não classifica bem, LLM lê diretamente
        raw = estruturado.get("texto_bruto") or ""
        if raw:
            raw = raw[:8000]

        context["curriculo"] = {
            "existe": True,
            "nome": estruturado.get("nome"),
            "stacks": skills,
            "experiencias_count": len(exp_list),
            "experiencias_resumo": "; ".join(resumo_exp),
            "projetos_count": len(estruturado.get("projetos") or []),
            "versao": curriculo.get("nome_versao") or f"v{curriculo.get('versao', 1)}",
            "texto_bruto": raw,
        }
    else:
        context["curriculo"] = {"existe": False}

    # Perfil profissional extraído do currículo
    profile = await db["profiles"].find_one({"user_id": user_id})
    if profile:
        context["profile"] = {
            "existe": True,
            "nome": profile.get("nome", ""),
            "titulo_profissional": profile.get("titulo_profissional", ""),
            "senioridade": profile.get("senioridade", ""),
            "anos_experiencia": profile.get("anos_experiencia", 0),
            "stack_principal": profile.get("stack_principal", []),
            "skills": profile.get("skills", {}),
            "idiomas": profile.get("idiomas", []),
        }
    else:
        context["profile"] = {"existe": False}

    if vaga_id:
        vaga = await db["vagas"].find_one({"_id": ObjectId(vaga_id)})
        if vaga:
            context["vaga_atual"] = {
                "id": vaga_id,
                "titulo": vaga.get("titulo", ""),
                "empresa": vaga.get("empresa", ""),
                "fonte": vaga.get("fonte", ""),
                "score": vaga.get("score", 50),
            }

    return context


# ─── System Prompt ────────────────────────────────────────────


def _build_system_prompt(user_id: str, context: dict) -> str:
    ctx_lines = ["## Contexto do Usuário"]

    vagas = context.get("vagas_recentes", [])
    if vagas:
        ctx_lines.append("\n**Últimas vagas:**")
        for v in vagas:
            ctx_lines.append(
                f"- [{v['id']}] {v['titulo']} @ {v['empresa']} (score: {v['score']})"
            )

    profile = context.get("profile")
    if profile and profile.get("existe"):
        stack_str = ", ".join(profile.get("stack_principal", [])) or "não informada"
        senioridade = profile.get("senioridade", "") or "não detectada"
        ctx_lines.append(
            f"\n**Perfil Profissional:** {profile.get('nome', 'Usuário')} "
            f"— {profile.get('titulo_profissional', '')}"
            f"\n**Senioridade:** {senioridade} | **Anos de exp:** {profile.get('anos_experiencia', 0)}"
            f"\n**Stack principal:** {stack_str}"
        )
        skills = profile.get("skills", {})
        if skills:
            cats = []
            for cat_name in (
                "frontend",
                "backend",
                "database",
                "cloud",
                "devops",
                "mobile",
                "ia",
                "outros",
            ):
                items = skills.get(cat_name, [])
                if items:
                    cats.append(f"{cat_name}: {', '.join(items)}")
            if cats:
                ctx_lines.append(f"\n**Skills detalhadas:**\n" + "\n".join(cats))
        idiomas = profile.get("idiomas", [])
        if idiomas:
            partes = []
            for i in idiomas:
                nome = i.get("nome", "")
                nivel = i.get("nivel", "")
                partes.append(f"{nome} ({nivel})")
            ctx_lines.append(f"\n**Idiomas:** {', '.join(partes)}")

    curriculo = context.get("curriculo", {})
    if curriculo.get("existe"):
        stacks = ", ".join(curriculo.get("stacks", [])) or "não informadas"
        exp_resumo = (
            curriculo.get("experiencias_resumo") or "nenhuma experiência detalhada"
        )
        ctx_lines.append(
            f"\n**Currículo Ativo ({curriculo.get('versao', '')}):** {curriculo.get('nome', 'Usuário')} — stacks: {stacks}\n"
            f"**Experiência ({curriculo.get('experiencias_count', 0)} total):** {exp_resumo}\n"
            f"**Projetos:** {curriculo.get('projetos_count', 0)} projetos catalogados"
        )

        raw = curriculo.get("texto_bruto", "")
        if raw and (
            curriculo.get("experiencias_count", 0) == 0
            or curriculo.get("projetos_count", 0) == 0
        ):
            ctx_lines.append(
                f"\n**Texto completo do currículo (fallback):**\n{raw[:5000]}"
            )
    else:
        ctx_lines.append("\n**Currículo:** nenhum (usuário ainda não fez upload)")

    pipe = context.get("pipeline_stats", {})
    pipe_total = context.get("pipeline_total", 0)
    if pipe_total > 0:
        ctx_lines.append(f"\n**Pipeline:** {pipe_total} candidaturas")
        active_stages = [
            s
            for s in [
                "salva",
                "aplicada",
                "em_analise",
                "entrevista_rh",
                "entrevista_tecnica",
                "teste_tecnico",
                "contratado",
            ]
            if pipe.get(s, 0) > 0
        ]
        if active_stages:
            ctx_lines.append(
                f"  - Ativas: {', '.join(f'{s}: {pipe.get(s, 0)}' for s in active_stages)}"
            )
        if pipe.get("rejeitado", 0) > 0:
            ctx_lines.append(f"  - Rejeitadas: {pipe['rejeitado']}")

    vaga_atual = context.get("vaga_atual")
    if vaga_atual:
        ctx_lines.append(
            f"\n**Vaga em contexto:** [{vaga_atual['id']}] {vaga_atual['titulo']} @ {vaga_atual['empresa']} (score: {vaga_atual['score']})"
        )

    context_str = "\n".join(ctx_lines)

    return f"""Você é o WorkPlus Copilot, assistente inteligente de carreira.

Você ajuda o usuário a otimizar candidaturas, analisar vagas, melhorar currículos e gerenciar o pipeline de forma estratégica.

{context_str}

## Regras Obrigatórias (não ignore)

### Anti-alucinação
- NUNCA invente skills, experiências, vagas, empresas, URLs, números ou dados que não estejam no contexto fornecido acima ou no histórico.
- SE NÃO SOUBER a resposta, diga "Não tenho essa informação no meu contexto atual" — não tente adivinhar.
- SE NÃO TIVER dados suficientes para uma análise, peça mais informações ao usuário.
- NUNCA simule resultados de ferramentas que não foram executadas — espere o resultado real da ferramenta.
- NUNCA gere links, URLs ou referências a vagas que não existem no banco de dados.

 ### Comportamento
- Seja direto, prático e profissional. Responda sempre em português.
- Use APENAS o contexto acima e o histórico da conversa para responder — não use conhecimento externo não verificado.
- Seja proativo: sugira análises, otimizações e ações estratégicas, mas apenas quando tiver dados reais para basear a sugestão.
- **NUNCA chame ferramentas sem o usuário pedir explicitamente.** Responda primeiro, depois pergunte se quer que execute algo.

### Uso de Ferramentas — Regra de Ouro
- **NUNCA inclua [TOOL:...] na sua resposta a menos que o usuário tenha acabado de pedir explicitamente aquela ação.**
- Se o usuário pedir análise de currículo, perfil, skills, ou informações: **responda usando apenas o contexto**. Depois pergunte se quer que faça algo com esses dados.
- Exemplo correto: "Suas skills principais são React, TypeScript, Next.js. Quer que eu busque vagas compatíveis?"
- Exemplo correto se o usuário responder "sim": "Claro! [TOOL:buscar_vagas|React TypeScript Next.js]"
- Exemplo ERRADO (não faça isso): responder com o tool marker sem o usuário ter confirmado.

### Formato de resposta
- Respostas curtas e objetivas. Parágrafos de no máximo 3 frases.
- Use listas apenas quando comparar múltiplos itens (ex: skills, vagas).
- NUNCA use markdown além de negrito (**) para ênfase.
- NUNCA use emojis.

## Ferramentas disponíveis
Inclua o marcador APENAS quando o usuário confirmar explicitamente que quer a ação:

- **analyze_vaga|vaga_id** — Análise profunda de uma vaga específica (requisitos, senioridade, ATS, etc.)
- **calcular_match|vaga_id** — Calcula compatibilidade entre vaga e currículo do usuário
- **analisar_match|vaga_id** — Analisa currículo vs vaga: destaca skills presentes/faltando, gaps, pontos fortes/fracos e sugestões de melhoria (NÃO modifica o currículo)
- **pipeline_status** — Mostra status completo do pipeline de candidaturas
- **buscar_vagas|termo** — Busca vagas na base consolidada. params pode ser texto simples (ex: "React remoto SP") ou JSON (ex: {{"busca": "React", "localizacao": "remoto"}}). Retorna até 15 vagas ranqueadas por score.
- **gerar_cover_letter|vaga_id** — Gera uma cover letter personalizada para a vaga

## Encadeamento de ações
APÓS executar uma ferramenta, SEMPRE sugira o próximo passo relevante:
- Após **analyze_vaga**: "Quer calcular o fit dessa vaga com seu perfil? [TOOL:calcular_match|vaga_id]"
- Após **calcular_match**: "Quer uma análise detalhada do match? [TOOL:analisar_match|vaga_id]" ou "Posso gerar uma cover letter. [TOOL:gerar_cover_letter|vaga_id]"
- Após **analisar_match**: "Quer que eu crie uma cover letter para acompanhar? [TOOL:gerar_cover_letter|vaga_id]"
- Após **pipeline_status**: "Quer analisar alguma vaga específica do pipeline?"
- Após **buscar_vagas**: "Qual das vagas acima te interessa? Posso analisar em detalhes ou calcular o match."

Usuário ID: {user_id}"""


def _detect_tool_call(text: str) -> Optional[dict]:
    match = re.search(r"\[TOOL:(\w+)(?:\|([^\]]+))?\]", text)
    if match:
        return {"tool": match.group(1), "params": match.group(2) or ""}
    return None


def _strip_tool_marker(text: str) -> str:
    return re.sub(r"\s*\[TOOL:\w+(?:\|[^\]]+)?\]\s*", "", text).strip()
