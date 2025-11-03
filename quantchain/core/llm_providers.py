"""LLM Provider abstractions for QuantChain agents."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import os
from dataclasses import dataclass

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import anthropic
except ImportError:
    anthropic = None

try:
    import ollama
except ImportError:
    ollama = None

try:
    from vllm import LLM
except ImportError:
    LLM = None


@dataclass
class LLMResponse:
    """Response from LLM provider."""

    text: str
    usage: Optional[Dict[str, Any]] = None
    finish_reason: Optional[str] = None


class LLMProvider(ABC):
    """Abstract base class for LLM providers."""

    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        """Generate response from LLM."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Get the model name."""
        pass


class OpenAIProvider(LLMProvider):
    """OpenAI LLM provider."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4") -> None:
        if OpenAI is None:
            raise ImportError("OpenAI package not installed")
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        self.client = OpenAI(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = self.client.chat.completions.create(
            model=self.model, messages=[{"role": "user", "content": prompt}], **kwargs
        )
        return LLMResponse(
            text=response.choices[0].message.content,
            usage=response.usage.model_dump() if response.usage else None,
            finish_reason=response.choices[0].finish_reason,
        )

    def get_model_name(self) -> str:
        return self.model


class AnthropicProvider(LLMProvider):
    """Anthropic Claude LLM provider."""

    def __init__(
        self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"
    ) -> None:
        if anthropic is None:
            raise ImportError("Anthropic package not installed")
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key required")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 1000),
            messages=[{"role": "user", "content": prompt}],
            **{k: v for k, v in kwargs.items() if k not in ["max_tokens"]},
        )
        return LLMResponse(
            text=response.content[0].text,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            finish_reason=response.stop_reason,
        )

    def get_model_name(self) -> str:
        return self.model


class OllamaProvider(LLMProvider):
    """Ollama local LLM provider."""

    def __init__(
        self, model: str = "llama2:7b", host: str = "http://localhost:11434"
    ) -> None:
        if ollama is None:
            raise ImportError("Ollama package not installed")
        self.model = model
        self.host = host

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        response = ollama.chat(
            model=self.model, messages=[{"role": "user", "content": prompt}], **kwargs
        )
        return LLMResponse(
            text=response["message"]["content"],
            finish_reason=response.get("done_reason"),
        )

    def get_model_name(self) -> str:
        return self.model


class VLLMProvider(LLMProvider):
    """vLLM local LLM provider."""

    def __init__(self, model: str, host: str = "http://localhost:8000") -> None:
        if LLM is None:
            raise ImportError("vLLM package not installed")
        self.model_name = model
        # For simplicity, assume vLLM is running as a server
        # In practice, might need to connect via HTTP client
        raise NotImplementedError("vLLM provider not yet implemented")

    def generate(self, prompt: str, **kwargs) -> LLMResponse:
        # Implement HTTP client to vLLM server
        raise NotImplementedError

    def get_model_name(self) -> str:
        return self.model_name


def create_llm_provider(provider_type: str, **kwargs) -> LLMProvider:  # type: ignore[return]
    """Factory function to create LLM provider."""
    providers = {
        "openai": OpenAIProvider,
        "anthropic": AnthropicProvider,
        "ollama": OllamaProvider,
        "vllm": VLLMProvider,
    }

    if provider_type not in providers:
        raise ValueError(f"Unsupported provider: {provider_type}")

    return providers[provider_type](**kwargs)
