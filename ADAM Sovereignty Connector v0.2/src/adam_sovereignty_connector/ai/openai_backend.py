"""OpenAI (and Azure OpenAI by configuration) backend."""
from __future__ import annotations

import os
from typing import List, Optional

from adam_sovereignty_connector.ai.base import AIBackend, Message, get_api_key


class OpenAIBackend(AIBackend):
    name = "openai"

    def __init__(
        self,
        model: str,
        api_key_env: str = "OPENAI_API_KEY",
        base_url: Optional[str] = None,
    ) -> None:
        self.model = model
        self.api_key = get_api_key(api_key_env)
        if not self.api_key:
            raise RuntimeError(
                f"OpenAI api key env var '{api_key_env}' is empty."
            )
        try:
            from openai import OpenAI  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "The 'openai' Python package is not installed."
            ) from e
        kwargs = {"api_key": self.api_key}
        if base_url:
            kwargs["base_url"] = base_url
        # Azure OpenAI detection via env (optional)
        if os.environ.get("AZURE_OPENAI_ENDPOINT"):
            kwargs["base_url"] = os.environ["AZURE_OPENAI_ENDPOINT"].rstrip("/") + "/openai/v1"
            kwargs["default_headers"] = {"api-key": self.api_key}
        self._client = OpenAI(**kwargs)

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
        choice = resp.choices[0]
        return choice.message.content or ""
