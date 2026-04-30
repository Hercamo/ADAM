"""Generic OpenAI-compatible backend (vLLM, LM Studio, together.ai, etc.)."""
from __future__ import annotations

from typing import List, Optional

from adam_sovereignty_connector.ai.base import AIBackend, Message, get_api_key


class OpenAICompatBackend(AIBackend):
    name = "openai_compat"

    def __init__(
        self,
        model: str,
        base_url: str,
        api_key_env: Optional[str] = "OPENAI_COMPAT_API_KEY",
    ) -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key = get_api_key(api_key_env) or "not-needed"
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "The 'openai' package is required for openai_compat (it talks v1/chat/completions)."
            ) from e
        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        resp = self._client.chat.completions.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return resp.choices[0].message.content or ""
