"""Anthropic Claude backend."""
from __future__ import annotations

from typing import List

from adam_sovereignty_connector.ai.base import AIBackend, Message, get_api_key


class AnthropicBackend(AIBackend):
    name = "anthropic"

    def __init__(self, model: str, api_key_env: str) -> None:
        self.model = model
        self.api_key = get_api_key(api_key_env)
        if not self.api_key:
            raise RuntimeError(
                f"ANTHROPIC api key env var '{api_key_env}' is empty. "
                "Set it before starting the connector or use a different backend."
            )
        try:
            import anthropic  # type: ignore
        except ImportError as e:  # pragma: no cover
            raise RuntimeError(
                "The 'anthropic' Python package is not installed. "
                "Add it to requirements.txt or install via `pip install anthropic`."
            ) from e
        self._client = anthropic.Anthropic(api_key=self.api_key)

    def chat(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        system_parts = [m.content for m in messages if m.role == "system"]
        chat_msgs = [
            {"role": m.role, "content": m.content}
            for m in messages if m.role in ("user", "assistant")
        ]
        resp = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system="\n\n".join(system_parts) if system_parts else None,
            messages=chat_msgs,
        )
        parts: List[str] = []
        for block in getattr(resp, "content", []):
            text = getattr(block, "text", None)
            if text:
                parts.append(text)
        return "".join(parts)
