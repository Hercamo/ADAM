"""
ADAM DNA Tool - AI Provider Abstraction Layer
Supports OpenAI, Anthropic (Claude), and Azure OpenAI with a unified interface.
Designed for easy extension to future model providers.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, AsyncIterator
from dataclasses import dataclass
import structlog

logger = structlog.get_logger()

@dataclass
class AIMessage:
    role: str  # system, user, assistant
    content: str

@dataclass
class AIResponse:
    content: str
    model: str
    provider: str
    usage: Dict[str, int]  # prompt_tokens, completion_tokens, total_tokens
    raw: Any = None

class AIProvider(ABC):
    """Abstract base for all AI model providers."""

    PROVIDER_NAME: str = "base"

    @abstractmethod
    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        """Send a chat completion request."""
        ...

    @abstractmethod
    async def chat_stream(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream a chat completion response."""
        ...

class OpenAIProvider(AIProvider):
    """OpenAI API provider (also compatible with Azure OpenAI when base_url is set)."""

    PROVIDER_NAME = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: Optional[str] = None):
        from openai import AsyncOpenAI
        self.model = model
        kwargs = {"api_key": api_key}
        if base_url:
            kwargs["base_url"] = base_url
        self.client = AsyncOpenAI(**kwargs)

    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.model,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return AIResponse(
            content=choice.message.content or "",
            model=self.model,
            provider=self.PROVIDER_NAME,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            raw=response,
        )

    async def chat_stream(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        stream = await self.client.chat.completions.create(
            model=self.model,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class AzureOpenAIProvider(AIProvider):
    """Azure OpenAI Service provider."""

    PROVIDER_NAME = "azure_openai"

    def __init__(self, api_key: str, endpoint: str, deployment: str, api_version: str = "2024-12-01-preview"):
        from openai import AsyncAzureOpenAI
        self.deployment = deployment
        self.client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )

    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        kwargs = {
            "model": self.deployment,
            "messages": msgs,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]

        return AIResponse(
            content=choice.message.content or "",
            model=self.deployment,
            provider=self.PROVIDER_NAME,
            usage={
                "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                "total_tokens": response.usage.total_tokens if response.usage else 0,
            },
            raw=response,
        )

    async def chat_stream(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        msgs = [{"role": m.role, "content": m.content} for m in messages]
        stream = await self.client.chat.completions.create(
            model=self.deployment,
            messages=msgs,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

class AnthropicProvider(AIProvider):
    """Anthropic Claude provider."""

    PROVIDER_NAME = "anthropic"

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-20250514"):
        from anthropic import AsyncAnthropic
        self.model = model
        self.client = AsyncAnthropic(api_key=api_key)

    async def chat(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
        json_mode: bool = False,
    ) -> AIResponse:
        # Anthropic uses a separate system parameter
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg += m.content + "\n"
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        if json_mode:
            system_msg += "\nIMPORTANT: Respond with valid JSON only. No markdown, no explanation."

        kwargs = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_msg.strip():
            kwargs["system"] = system_msg.strip()

        response = await self.client.messages.create(**kwargs)

        content = ""
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text

        return AIResponse(
            content=content,
            model=self.model,
            provider=self.PROVIDER_NAME,
            usage={
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            },
            raw=response,
        )

    async def chat_stream(
        self,
        messages: List[AIMessage],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        system_msg = ""
        chat_messages = []
        for m in messages:
            if m.role == "system":
                system_msg += m.content + "\n"
            else:
                chat_messages.append({"role": m.role, "content": m.content})

        kwargs = {
            "model": self.model,
            "messages": chat_messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if system_msg.strip():
            kwargs["system"] = system_msg.strip()

        async with self.client.messages.stream(**kwargs) as stream:
            async for text in stream.text_stream:
                yield text

def create_provider(
    provider_name: str,
    openai_key: Optional[str] = None,
    openai_model: str = "gpt-4o",
    openai_base_url: Optional[str] = None,
    anthropic_key: Optional[str] = None,
    anthropic_model: str = "claude-sonnet-4-20250514",
    azure_key: Optional[str] = None,
    azure_endpoint: Optional[str] = None,
    azure_deployment: Optional[str] = None,
    azure_api_version: str = "2024-12-01-preview",
) -> AIProvider:
    """Factory function to create the appropriate AI provider."""
    if provider_name == "openai":
        if not openai_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAI provider")
        return OpenAIProvider(api_key=openai_key, model=openai_model, base_url=openai_base_url)

    elif provider_name == "anthropic":
        if not anthropic_key:
            raise ValueError("ANTHROPIC_API_KEY is required for Anthropic provider")
        return AnthropicProvider(api_key=anthropic_key, model=anthropic_model)

    elif provider_name == "azure_openai":
        if not all([azure_key, azure_endpoint, azure_deployment]):
            raise ValueError("Azure OpenAI requires API key, endpoint, and deployment name")
        return AzureOpenAIProvider(
            api_key=azure_key,
            endpoint=azure_endpoint,
            deployment=azure_deployment,
            api_version=azure_api_version,
        )

    else:
        raise ValueError(f"Unknown AI provider: {provider_name}. Supported: openai, anthropic, azure_openai")
