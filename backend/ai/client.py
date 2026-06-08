import asyncio
import json
import re
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import AsyncGenerator, Optional

import httpx
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from core.config import settings
from core.logger import logger

PROVIDERS = ["ollama", "lm_studio"]
_provider_override: Optional[str] = None


def set_provider(name: str) -> None:
    global _provider_override
    if name not in PROVIDERS:
        raise ValueError(f"Provider invalido. Opcoes: {', '.join(PROVIDERS)}")
    _provider_override = name


def get_active_provider() -> str:
    return _provider_override or settings.ai_provider_primary


def get_provider_info() -> dict:
    provider = get_active_provider()
    models = {
        "ollama": settings.ollama_model,
        "lm_studio": settings.lm_studio_model,
    }
    return {
        "current": provider,
        "available": PROVIDERS,
        "models": models,
    }


PROMPTS_DIR = Path(__file__).parent / "prompts"

_jinja_env = Environment(loader=FileSystemLoader(str(PROMPTS_DIR)))


def _render_prompt(name: str, **kwargs) -> str:
    try:
        tpl = _jinja_env.get_template(name)
        return tpl.render(**kwargs)
    except TemplateNotFound:
        logger.warning("ai.prompt_nao_encontrado", name=name)
        raise


class CircuitBreaker:
    def __init__(self, threshold: int, reset_seconds: int):
        self.threshold = threshold
        self.reset_seconds = reset_seconds
        self.failures = 0
        self.last_failure: Optional[datetime] = None
        self.state = "closed"

    def record_success(self):
        self.failures = 0
        self.state = "closed"

    def record_failure(self):
        self.failures += 1
        self.last_failure = datetime.utcnow()
        if self.failures >= self.threshold:
            self.state = "open"

    def is_open(self) -> bool:
        if self.state == "open" and self.last_failure:
            if (
                datetime.utcnow() - self.last_failure
            ).total_seconds() > self.reset_seconds:
                self.state = "half-open"
                return False
            return True
        return False


_PROVIDER_CONFIGS = {
    "lm_studio": lambda: {
        "url": f"{settings.lm_studio_url.rstrip('/')}/v1/chat/completions",
        "model": settings.lm_studio_model,
    },
    "ollama": lambda: {
        "url": f"{settings.ollama_url.rstrip('/')}/v1/chat/completions",
        "model": settings.ollama_model,
    },
    "openrouter": lambda: {
        "url": settings.openrouter_url,
        "model": settings.openrouter_model,
        "api_key": settings.openrouter_api_key,
    },
}

_circuit_breaker = CircuitBreaker(
    threshold=settings.ai_circuit_breaker_threshold,
    reset_seconds=settings.ai_circuit_breaker_reset,
)


async def _call_provider(
    provider: str,
    messages: list,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 120,
) -> Optional[str]:
    cfg_fn = _PROVIDER_CONFIGS.get(provider)
    if not cfg_fn:
        logger.warning("ai.provedor_desconhecido", provider=provider)
        return None

    cfg = cfg_fn()
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }

    headers = {"Content-Type": "application/json"}
    if provider == "openrouter" and cfg.get("api_key"):
        headers["Authorization"] = f"Bearer {cfg['api_key']}"
        if settings.openrouter_site_url:
            headers["HTTP-Referer"] = settings.openrouter_site_url
        if settings.openrouter_site_name:
            headers["X-Title"] = settings.openrouter_site_name

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.post(cfg["url"], json=payload, headers=headers)
            resp.raise_for_status()
            msg = resp.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning_content") or ""
            return content.strip() if content else None
    except Exception as e:
        logger.warning("ai.provedor_erro", provider=provider, error=str(e))
        return None


async def _call_with_retry(
    messages: list,
    temperature: float = 0.1,
    max_tokens: int = 2048,
    timeout: int = 120,
) -> Optional[str]:
    active = get_active_provider()
    providers = [active]

    for attempt in range(settings.ai_retry_max):
        for provider in providers:
            if _circuit_breaker.is_open():
                logger.warning("ai.circuit_breaker_aberto", provider=provider)
                continue

            result = await _call_provider(
                provider, messages, temperature, max_tokens, timeout
            )
            if result:
                _circuit_breaker.record_success()
                return result

            _circuit_breaker.record_failure()

        if attempt < settings.ai_retry_max - 1:
            delay = settings.ai_retry_base_delay * (2**attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)

    logger.error("ai.todas_tentativas_falharam")
    return None


def _parse_json(text: str) -> Optional[dict]:
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None


async def analisar_vaga(
    titulo: str, descricao: str, empresa: str = "", fonte: str = ""
) -> Optional[dict]:
    prompt = _render_prompt(
        "vaga_analysis.j2",
        titulo=titulo,
        descricao=descricao[:4000],
        empresa=empresa,
        fonte=fonte,
    )
    messages = [{"role": "user", "content": prompt}]
    result = await _call_with_retry(messages, temperature=0.1, max_tokens=2048)
    if not result:
        return None
    return _parse_json(result)


async def calcular_match(
    vaga_titulo: str = "",
    vaga_empresa: str = "",
    vaga_requisitos: str = "",
    vaga_desejaveis: str = "",
    vaga_stack: str = "",
    vaga_senioridade: str = "",
    perfil_stacks: str = "",
    perfil_experiencias: str = "",
    perfil_senioridade: str = "",
    perfil_projetos: str = "",
    score_algoritmico: int = 50,
) -> Optional[dict]:
    prompt = _render_prompt(
        "match_scoring.j2",
        vaga_titulo=vaga_titulo,
        vaga_empresa=vaga_empresa,
        vaga_requisitos=vaga_requisitos,
        vaga_desejaveis=vaga_desejaveis,
        vaga_stack=vaga_stack,
        vaga_senioridade=vaga_senioridade,
        perfil_stacks=perfil_stacks,
        perfil_experiencias=perfil_experiencias,
        perfil_senioridade=perfil_senioridade,
        perfil_projetos=perfil_projetos,
        score_algoritmico=score_algoritmico,
    )
    messages = [{"role": "user", "content": prompt}]
    result = await _call_with_retry(messages, temperature=0.1, max_tokens=2048)
    if not result:
        return None
    return _parse_json(result)


async def gerar_cover_letter(
    vaga_empresa: str = "",
    vaga_titulo: str = "",
    vaga_descricao: str = "",
    perfil_nome: str = "",
    perfil_resumo: str = "",
    perfil_stacks: str = "",
) -> Optional[dict]:
    prompt = _render_prompt(
        "cover_letter.j2",
        vaga_empresa=vaga_empresa,
        vaga_titulo=vaga_titulo,
        vaga_descricao=vaga_descricao,
        perfil_nome=perfil_nome,
        perfil_resumo=perfil_resumo,
        perfil_stacks=perfil_stacks,
    )
    messages = [{"role": "user", "content": prompt}]
    result = await _call_with_retry(messages, temperature=0.3, max_tokens=1024)
    if not result:
        return None
    return _parse_json(result)


async def chat_stream(
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[str, None]:
    active = get_active_provider()
    providers = [active]

    for provider in providers:
        if _circuit_breaker.is_open():
            logger.warning("ai.circuit_breaker_aberto_stream", provider=provider)
            continue

        cfg_fn = _PROVIDER_CONFIGS.get(provider)
        if not cfg_fn:
            continue

        cfg = cfg_fn()
        payload = {
            "model": cfg["model"],
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
            "stream": True,
        }

        headers = {"Content-Type": "application/json"}
        if provider == "openrouter" and cfg.get("api_key"):
            headers["Authorization"] = f"Bearer {cfg['api_key']}"
            if settings.openrouter_site_url:
                headers["HTTP-Referer"] = settings.openrouter_site_url
            if settings.openrouter_site_name:
                headers["X-Title"] = settings.openrouter_site_name
        url = cfg["url"]

        try:
            async with httpx.AsyncClient(timeout=180) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=headers
                ) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if line.startswith("data: "):
                            data_str = line[6:].strip()
                            if data_str == "[DONE]":
                                break
                            try:
                                data = json.loads(data_str)
                                delta = data.get("choices", [{}])[0].get("delta", {})
                                reasoning = delta.get("reasoning_content", "")
                                if reasoning:
                                    yield {"type": "reasoning", "token": reasoning}
                                content = delta.get("content", "")
                                if content:
                                    yield {"type": "content", "token": content}
                            except json.JSONDecodeError:
                                continue
            _circuit_breaker.record_success()
            return
        except Exception as e:
            logger.warning("ai.stream_erro", provider=provider, error=str(e))
            _circuit_breaker.record_failure()
            continue

    yield "\n\nDesculpe, nÃ£o consegui processar sua mensagem no momento. Tente novamente mais tarde."
