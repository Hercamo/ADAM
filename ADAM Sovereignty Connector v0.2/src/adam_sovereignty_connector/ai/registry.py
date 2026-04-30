"""Factory for AI backends."""
from __future__ import annotations

from typing import List

from adam_sovereignty_connector.ai.base import AIBackend
from adam_sovereignty_connector.config import AIBackendConfig


def available_backends() -> List[str]:
    return ["anthropic", "openai", "ollama", "openai_compat"]


def get_backend(cfg: AIBackendConfig) -> AIBackend:
    kind = (cfg.kind or "").lower()
    if kind == "anthropic":
        from adam_sovereignty_connector.ai.anthropic_backend import AnthropicBackend
        return AnthropicBackend(model=cfg.model, api_key_env=cfg.api_key_env)
    if kind == "openai":
        from adam_sovereignty_connector.ai.openai_backend import OpenAIBackend
        return OpenAIBackend(
            model=cfg.model, api_key_env=cfg.api_key_env, base_url=cfg.base_url
        )
    if kind == "ollama":
        from adam_sovereignty_connector.ai.ollama_backend import OllamaBackend
        return OllamaBackend(model=cfg.model, base_url=cfg.base_url or "http://127.0.0.1:11434")
    if kind == "openai_compat":
        from adam_sovereignty_connector.ai.openai_compat_backend import OpenAICompatBackend
        if not cfg.base_url:
            raise ValueError("openai_compat requires a base_url")
        return OpenAICompatBackend(
            model=cfg.model, base_url=cfg.base_url, api_key_env=cfg.api_key_env
        )
    raise ValueError(f"Unknown AI backend kind: {cfg.kind!r}")
