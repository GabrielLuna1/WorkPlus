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


def _ollama_base() -> str:
    return settings.ollama_url.rstrip("/")


def reset_circuit_breaker() -> None:
    _circuit_breaker.reset()


async def gpu_load() -> dict:
    active = get_active_provider()
    if active == "lm_studio":
        return {
            "status": "always_loaded",
            "model": settings.lm_studio_model,
            "note": "LM Studio gerencia a GPU automaticamente",
        }
    url = f"{_ollama_base()}/api/generate"
    model = settings.ollama_model
    payload = {"model": model, "prompt": "", "keep_alive": -1, "stream": False}
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return {"status": "loaded", "model": model}


async def gpu_unload() -> dict:
    active = get_active_provider()
    if active == "lm_studio":
        return {
            "status": "always_loaded",
            "model": settings.lm_studio_model,
            "note": "LM Studio gerencia a GPU automaticamente",
        }
    url = f"{_ollama_base()}/api/generate"
    model = settings.ollama_model
    payload = {"model": model, "prompt": "", "keep_alive": 0, "stream": False}
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(url, json=payload)
        resp.raise_for_status()
        return {"status": "unloaded", "model": model}


async def gpu_status() -> dict:
    active = get_active_provider()
    if active == "lm_studio":
        return {
            "loaded": True,
            "model": settings.lm_studio_model,
            "vram_bytes": 0,
            "note": "LM Studio gerenciamento externo",
        }
    url = f"{_ollama_base()}/api/ps"
    model = settings.ollama_model
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()
        loaded = [m for m in data.get("models", []) if m.get("name") == model]
        if loaded:
            m = loaded[0]
            return {"loaded": True, "model": model, "vram_bytes": m.get("size_vram", 0)}
        return {"loaded": False, "model": model, "vram_bytes": 0}


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


async def _chat_stream_lm_studio(
    messages: list,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[dict, None]:
    cfg_fn = _PROVIDER_CONFIGS.get("lm_studio")
    if not cfg_fn:
        return
    cfg = cfg_fn()
    payload = {
        "model": cfg["model"],
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": True,
    }
    url = cfg["url"]
    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, json=payload) as resp:
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


async def _chat_stream_ollama(
    messages: list,
    temperature: float,
    max_tokens: int,
) -> AsyncGenerator[dict, None]:
    base = _ollama_base()
    payload = {
        "model": settings.ollama_model,
        "messages": messages,
        "options": {
            "temperature": temperature,
            "num_predict": max_tokens,
        },
        "stream": True,
    }
    url = f"{base}/api/chat"
    thinking_buffer = ""
    in_thinking = False
    think_open_emitted = False

    async with httpx.AsyncClient(timeout=180) as client:
        async with client.stream("POST", url, json=payload) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if not line.strip():
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                thinking = data.get("message", {}).get("thinking", "")
                content = data.get("message", {}).get("content", "")

                if thinking:
                    yield {"type": "reasoning", "token": thinking}

                if not content:
                    if data.get("done"):
                        break
                    continue

                if not think_open_emitted:
                    think_open_emitted = True

                # Track think tags in streaming content
                while content:
                    if not in_thinking:
                        idx = content.find("<think>")
                        if idx == -1:
                            yield {"type": "content", "token": content}
                            break
                        else:
                            before = content[:idx]
                            if before:
                                yield {"type": "content", "token": before}
                            in_thinking = True
                            content = content[idx + 7 :]
                    else:
                        idx = content.find("</think>")
                        if idx == -1:
                            thinking_buffer += content
                            yield {"type": "reasoning", "token": content}
                            break
                        else:
                            before = content[:idx]
                            if before:
                                thinking_buffer += before
                                yield {"type": "reasoning", "token": before}
                            in_thinking = False
                            content = content[idx + 8 :]

    # If thinking tag never closed, flush as content
    if in_thinking and thinking_buffer:
        yield {"type": "content", "token": thinking_buffer}


_STREAM_HANDLERS = {
    "ollama": _chat_stream_ollama,
    "lm_studio": _chat_stream_lm_studio,
}


async def chat_stream(
    messages: list,
    temperature: float = 0.7,
    max_tokens: int = 2048,
) -> AsyncGenerator[dict, None]:
    active = get_active_provider()
    providers = [active]

    for provider in providers:
        if _circuit_breaker.is_open():
            logger.warning("ai.circuit_breaker_aberto_stream", provider=provider)
            continue

        handler = _STREAM_HANDLERS.get(provider)
        if not handler:
            logger.warning("ai.sem_handler_stream", provider=provider)
            continue

        try:
            async for event in handler(messages, temperature, max_tokens):
                yield event
            _circuit_breaker.record_success()
            return
        except Exception as e:
            logger.warning("ai.stream_erro", provider=provider, error=str(e))
            _circuit_breaker.record_failure()
            continue

    yield {
        "type": "error",
        "token": "\n\nDesculpe, não consegui processar sua mensagem no momento. Tente novamente mais tarde.",
    }
