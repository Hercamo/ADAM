"""Common interface for AI backends.

The connector uses this interface only inside the HTTP /ai/chat endpoint and
small "explain-this" helpers. The primary control path is MCP: the model
invokes catalog tools directly, so we do NOT need a huge tool-calling agent
loop here. Keeping this surface narrow keeps the attack surface small.
"""
from __future__ import annotations

import abc
import os
from dataclasses import dataclass
from typing import Iterable, List, Optional


@dataclass
class Message:
    role: str        # "system" | "user" | "assistant"
    content: str


class AIBackend(abc.ABC):
    name: str = "base"

    @abc.abstractmethod
    def chat(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        """Synchronous request/response."""

    def stream(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Iterable[str]:
        """Default streaming implementation: yield the whole response once."""
        yield self.chat(messages, max_tokens=max_tokens, temperature=temperature)


def get_api_key(env_var: Optional[str]) -> Optional[str]:
    if not env_var:
        return None
    return os.environ.get(env_var)
