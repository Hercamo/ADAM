"""Ollama local-model backend.

Perfect for the air-gapped showcase: Ollama runs entirely on the same box
and exposes an HTTP API at http://127.0.0.1:11434 by default.
"""
from __future__ import annotations

import json
from typing import Iterable, List

import urllib.request

from adam_sovereignty_connector.ai.base import AIBackend, Message


class OllamaBackend(AIBackend):
    name = "ollama"

    def __init__(self, model: str, base_url: str = "http://127.0.0.1:11434") -> None:
        self.model = model
        self.base_url = base_url.rstrip("/")

    def chat(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> str:
        body = {
            "model": self.model,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data.get("message", {}).get("content", "")

    def stream(
        self,
        messages: List[Message],
        *,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> Iterable[str]:
        body = {
            "model": self.model,
            "stream": True,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
            "messages": [{"role": m.role, "content": m.content} for m in messages],
        }
        req = urllib.request.Request(
            f"{self.base_url}/api/chat",
            data=json.dumps(body).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=300) as resp:
            for line in resp:
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line.decode("utf-8"))
                except Exception:
                    continue
                chunk = obj.get("message", {}).get("content")
                if chunk:
                    yield chunk
                if obj.get("done"):
                    break
