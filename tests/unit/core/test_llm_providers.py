"""Comprehensive tests for LLM Providers."""

import os
from unittest.mock import Mock, patch

import pytest

from quantchain.core.llm_providers import (
    AnthropicProvider,
    LLMProvider,
    LLMResponse,
    OllamaProvider,
    OpenAIProvider,
    VLLMProvider,
    create_llm_provider,
)


@pytest.mark.unit
class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_llm_response_creation(self):
        """Test creating LLMResponse with all fields."""
        usage = {"prompt_tokens": 10, "completion_tokens": 20}
        response = LLMResponse(text="Test response", usage=usage, finish_reason="stop")

        assert response.text == "Test response"
        assert response.usage == usage
        assert response.finish_reason == "stop"

    def test_llm_response_creation_minimal(self):
        """Test creating LLMResponse with minimal fields."""
        response = LLMResponse(text="Test response")

        assert response.text == "Test response"
        assert response.usage is None
        assert response.finish_reason is None

    def test_llm_response_empty_text(self):
        """Test creating LLMResponse with empty text."""
        response = LLMResponse(text="")

        assert response.text == ""
        assert response.usage is None
        assert response.finish_reason is None


@pytest.mark.unit
class TestLLMProvider:
    """Test LLMProvider abstract base class."""

    def test_llm_provider_is_abstract(self):
        """Test that LLMProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_llm_provider_abstract_methods(self):
        """Test that LLMProvider requires abstract methods."""

        # Create a concrete implementation for testing
        class TestProvider(LLMProvider):
            def generate(self, prompt: str, **kwargs):
                return LLMResponse(text="test")

            def get_model_name(self) -> str:
                return "test-model"

        provider = TestProvider()
        assert hasattr(provider, "generate")
        assert hasattr(provider, "get_model_name")


@pytest.mark.unit
class TestOpenAIProvider:
    """Test OpenAIProvider class."""

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_init_with_api_key(self, mock_openai_class):
        """Test OpenAI provider initialization with API key."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-3.5-turbo"
        assert provider.client == mock_client
        mock_openai_class.assert_called_once_with(api_key="test-key")

    @patch("quantchain.core.llm_providers.OpenAI")
    @patch.dict(os.environ, {"OPENAI_API_KEY": "env-key"})
    def test_openai_provider_init_from_env(self, mock_openai_class):
        """Test OpenAI provider initialization from environment variable."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider()

        assert provider.api_key == "env-key"
        assert provider.model == "gpt-4"  # default model
        mock_openai_class.assert_called_once_with(api_key="env-key")

    @patch("quantchain.core.llm_providers.OpenAI", None)
    def test_openai_provider_no_package(self):
        """Test OpenAI provider initialization when package is not installed."""
        with pytest.raises(ImportError, match="OpenAI package not installed"):
            OpenAIProvider()

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_no_api_key(self, mock_openai_class):
        """Test OpenAI provider initialization without API key."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Remove environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                OpenAIProvider()

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_generate(self, mock_openai_class):
        """Test OpenAI provider text generation."""
        # Mock the OpenAI client
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock the response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = Mock()
        mock_response.usage.model_dump.return_value = {
            "prompt_tokens": 10,
            "completion_tokens": 20,
        }

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        response = provider.generate("Test prompt", max_tokens=100, temperature=0.7)

        assert response.text == "Generated text"
        assert response.usage == {"prompt_tokens": 10, "completion_tokens": 20}
        assert response.finish_reason == "stop"

        # Verify the API was called correctly
        mock_client.chat.completions.create.assert_called_once_with(
            model="gpt-4",
            messages=[{"role": "user", "content": "Test prompt"}],
            max_tokens=100,
            temperature=0.7,
        )

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_generate_no_usage(self, mock_openai_class):
        """Test OpenAI provider generation without usage info."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        # Mock response without usage
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")
        response = provider.generate("Test prompt")

        assert response.text == "Generated text"
        assert response.usage is None
        assert response.finish_reason == "stop"

    def test_openai_provider_get_model_name(self):
        """Test getting model name from OpenAI provider."""
        with patch("quantchain.core.llm_providers.OpenAI") as mock_openai_class:
            mock_client = Mock()
            mock_openai_class.return_value = mock_client

            provider = OpenAIProvider(api_key="test-key", model="gpt-3.5-turbo")
            assert provider.get_model_name() == "gpt-3.5-turbo"

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_default_model(self, mock_openai_class):
        """Test OpenAI provider default model."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key")
        assert provider.model == "gpt-4"


@pytest.mark.unit
class TestAnthropicProvider:
    """Test AnthropicProvider class."""

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_init_with_api_key(self, mock_anthropic):
        """Test Anthropic provider initialization with API key."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        provider = AnthropicProvider(
            api_key="test-key", model="claude-3-haiku-20240307"
        )

        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-haiku-20240307"
        assert provider.client == mock_client
        mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")

    @patch("quantchain.core.llm_providers.anthropic")
    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "env-key"})
    def test_anthropic_provider_init_from_env(self, mock_anthropic):
        """Test Anthropic provider initialization from environment variable."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        provider = AnthropicProvider()

        assert provider.api_key == "env-key"
        assert provider.model == "claude-3-sonnet-20240229"  # default model
        mock_anthropic.Anthropic.assert_called_once_with(api_key="env-key")

    @patch("quantchain.core.llm_providers.anthropic", None)
    def test_anthropic_provider_no_package(self):
        """Test Anthropic provider initialization when package is not installed."""
        with pytest.raises(ImportError, match="Anthropic package not installed"):
            AnthropicProvider()

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_no_api_key(self, mock_anthropic):
        """Test Anthropic provider initialization without API key."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Remove environment variable
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Anthropic API key required"):
                AnthropicProvider()

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_generate(self, mock_anthropic):
        """Test Anthropic provider text generation."""
        # Mock the Anthropic client
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        # Mock the response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Generated text"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        response = provider.generate("Test prompt", max_tokens=100, temperature=0.7)

        assert response.text == "Generated text"
        assert response.usage == {"input_tokens": 10, "output_tokens": 20}
        assert response.finish_reason == "end_turn"

        # Verify the API was called correctly
        mock_client.messages.create.assert_called_once_with(
            model="claude-3-sonnet-20240229",
            max_tokens=100,
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
        )

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_generate_with_default_max_tokens(self, mock_anthropic):
        """Test Anthropic provider generation with default max_tokens."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Generated text"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")
        provider.generate("Test prompt")  # No max_tokens specified

        # Verify default max_tokens was used
        call_args = mock_client.messages.create.call_args
        assert call_args[1]["max_tokens"] == 1000

    def test_anthropic_provider_get_model_name(self):
        """Test getting model name from Anthropic provider."""
        with patch("quantchain.core.llm_providers.anthropic") as mock_anthropic:
            mock_client = Mock()
            mock_anthropic.Anthropic.return_value = mock_client

            provider = AnthropicProvider(
                api_key="test-key", model="claude-3-haiku-20240307"
            )
            assert provider.get_model_name() == "claude-3-haiku-20240307"

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_default_model(self, mock_anthropic):
        """Test Anthropic provider default model."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        provider = AnthropicProvider(api_key="test-key")
        assert provider.model == "claude-3-sonnet-20240229"


@pytest.mark.unit
class TestOllamaProvider:
    """Test OllamaProvider class."""

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_init(self, mock_ollama):
        """Test Ollama provider initialization."""
        provider = OllamaProvider(model="llama2:7b", host="http://localhost:11435")

        assert provider.model == "llama2:7b"
        assert provider.host == "http://localhost:11435"

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_default_values(self, mock_ollama):
        """Test Ollama provider default values."""
        provider = OllamaProvider()

        assert provider.model == "llama2:7b"
        assert provider.host == "http://localhost:11434"

    @patch("quantchain.core.llm_providers.ollama", None)
    def test_ollama_provider_no_package(self):
        """Test Ollama provider initialization when package is not installed."""
        with pytest.raises(ImportError, match="Ollama package not installed"):
            OllamaProvider()

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_generate(self, mock_ollama):
        """Test Ollama provider text generation."""
        # Mock the ollama response
        mock_response = {
            "message": {"content": "Generated text"},
            "done_reason": "stop",
        }
        mock_ollama.chat.return_value = mock_response

        provider = OllamaProvider(model="llama2:7b")
        response = provider.generate("Test prompt", temperature=0.7)

        assert response.text == "Generated text"
        assert response.usage is None
        assert response.finish_reason == "stop"

        # Verify the API was called correctly
        mock_ollama.chat.assert_called_once_with(
            model="llama2:7b",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
        )

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_generate_no_finish_reason(self, mock_ollama):
        """Test Ollama provider generation without finish reason."""
        mock_response = {
            "message": {"content": "Generated text"}
            # No done_reason
        }
        mock_ollama.chat.return_value = mock_response

        provider = OllamaProvider()
        response = provider.generate("Test prompt")

        assert response.text == "Generated text"
        assert response.usage is None
        assert response.finish_reason is None

    def test_ollama_provider_get_model_name(self):
        """Test getting model name from Ollama provider."""
        with patch("quantchain.core.llm_providers.ollama"):
            provider = OllamaProvider(model="codellama:7b")
            assert provider.get_model_name() == "codellama:7b"


@pytest.mark.unit
class TestVLLMProvider:
    """Test VLLMProvider class."""

    @patch("quantchain.core.llm_providers.LLM")
    def test_vllm_provider_init(self, mock_llm):
        """Test VLLM provider initialization."""
        provider = VLLMProvider(model="llama2:7b", host="http://localhost:8001")

        assert provider.model_name == "llama2:7b"
        assert provider.host == "http://localhost:8001"

    @patch("quantchain.core.llm_providers.LLM")
    def test_vllm_provider_default_host(self, mock_llm):
        """Test VLLM provider default host."""
        provider = VLLMProvider(model="llama2:7b")

        assert provider.model_name == "llama2:7b"
        assert provider.host == "http://localhost:8000"

    @patch("quantchain.core.llm_providers.LLM", None)
    def test_vllm_provider_no_package(self):
        """Test VLLM provider initialization when package is not installed."""
        with pytest.raises(ImportError, match="vLLM package not installed"):
            VLLMProvider("test-model")

    @patch("quantchain.core.llm_providers.LLM")
    def test_vllm_provider_not_implemented(self, mock_llm):
        """Test VLLM provider methods are not implemented."""
        provider = VLLMProvider("test-model")

        # generate method should raise NotImplementedError
        with pytest.raises(
            NotImplementedError, match="vLLM provider not yet implemented"
        ):
            provider.generate("test prompt")

    @patch("quantchain.core.llm_providers.LLM")
    def test_vllm_provider_generate_not_implemented(self, mock_llm):
        """Test VLLM provider generate method is not implemented."""
        # Skip initialization NotImplementedError
        with patch.object(
            VLLMProvider,
            "__init__",
            lambda self, model, host="http://localhost:8000": None,
        ):
            provider = VLLMProvider("test-model")
            provider.model_name = "test-model"

            with pytest.raises(NotImplementedError):
                provider.generate("Test prompt")

    def test_vllm_provider_get_model_name(self):
        """Test getting model name from VLLM provider."""
        with patch("quantchain.core.llm_providers.LLM"):
            # Skip initialization NotImplementedError
            with patch.object(
                VLLMProvider,
                "__init__",
                lambda self, model, host="http://localhost:8000": None,
            ):
                provider = VLLMProvider("test-model")
                provider.model_name = "test-model"
                assert provider.get_model_name() == "test-model"


@pytest.mark.unit
class TestCreateLLMProvider:
    """Test create_llm_provider factory function."""

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_create_openai_provider(self, mock_openai_class):
        """Test creating OpenAI provider through factory."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        provider = create_llm_provider(
            "openai", api_key="test-key", model="gpt-3.5-turbo"
        )

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "test-key"
        assert provider.model == "gpt-3.5-turbo"

    @patch("quantchain.core.llm_providers.anthropic")
    def test_create_anthropic_provider(self, mock_anthropic):
        """Test creating Anthropic provider through factory."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        provider = create_llm_provider("anthropic", api_key="test-key")

        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "test-key"

    @patch("quantchain.core.llm_providers.ollama")
    def test_create_ollama_provider(self, mock_ollama):
        """Test creating Ollama provider through factory."""
        provider = create_llm_provider("ollama", model="llama2:7b")

        assert isinstance(provider, OllamaProvider)
        assert provider.model == "llama2:7b"

    def test_create_unsupported_provider(self):
        """Test creating unsupported provider type."""
        with pytest.raises(ValueError, match="Unsupported provider: unsupported"):
            create_llm_provider("unsupported")

    @patch("quantchain.core.llm_providers.LLM")
    def test_create_vllm_provider_not_supported(self, mock_llm):
        """Test that VLLM provider is not supported in factory."""
        with pytest.raises(ValueError, match="Unsupported provider: vllm"):
            create_llm_provider("vllm", model="test-model")


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error conditions."""

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_empty_api_key(self, mock_openai_class):
        """Test OpenAI provider with empty API key."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                OpenAIProvider(api_key="")

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_empty_api_key(self, mock_anthropic):
        """Test Anthropic provider with empty API key."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="Anthropic API key required"):
                AnthropicProvider(api_key="")

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_empty_model_name(self, mock_openai_class):
        """Test OpenAI provider with empty model name."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        provider = OpenAIProvider(api_key="test-key", model="")
        assert provider.model == ""

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_empty_model_name(self, mock_ollama):
        """Test Ollama provider with empty model name."""
        provider = OllamaProvider(model="")
        assert provider.model == ""

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_generate_with_kwargs(self, mock_openai_class):
        """Test OpenAI provider generation with various kwargs."""
        mock_client = Mock()
        mock_openai_class.return_value = mock_client

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        provider = OpenAIProvider(api_key="test-key")

        # Test with various kwargs
        kwargs = {
            "max_tokens": 100,
            "temperature": 0.7,
            "top_p": 0.9,
            "frequency_penalty": 0.5,
            "presence_penalty": 0.3,
        }
        provider.generate("Test prompt", **kwargs)

        # Verify all kwargs were passed through
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]

        assert call_kwargs["model"] == "gpt-4"
        assert call_kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]
        assert call_kwargs["max_tokens"] == 100
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.5
        assert call_kwargs["presence_penalty"] == 0.3

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_generate_with_kwargs(self, mock_anthropic):
        """Test Anthropic provider generation with various kwargs."""
        mock_client = Mock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Generated text"
        mock_response.stop_reason = "end_turn"
        mock_response.usage = Mock()
        mock_response.usage.input_tokens = 10
        mock_response.usage.output_tokens = 20

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="test-key")

        # Test with various kwargs, including max_tokens which should be handled specially
        kwargs = {"max_tokens": 200, "temperature": 0.7, "top_p": 0.9}
        provider.generate("Test prompt", **kwargs)

        # Verify kwargs were passed through correctly
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]

        assert call_kwargs["model"] == "claude-3-sonnet-20240229"
        assert call_kwargs["max_tokens"] == 200  # Should be extracted from kwargs
        assert call_kwargs["messages"] == [{"role": "user", "content": "Test prompt"}]
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["top_p"] == 0.9

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_generate_with_kwargs(self, mock_ollama):
        """Test Ollama provider generation with various kwargs."""
        mock_response = {
            "message": {"content": "Generated text"},
            "done_reason": "stop",
        }
        mock_ollama.chat.return_value = mock_response

        provider = OllamaProvider()

        # Test with various kwargs
        kwargs = {"temperature": 0.7, "top_p": 0.9, "num_ctx": 2048}
        provider.generate("Test prompt", **kwargs)

        # Verify all kwargs were passed through
        mock_ollama.chat.assert_called_once_with(
            model="llama2:7b",
            messages=[{"role": "user", "content": "Test prompt"}],
            temperature=0.7,
            top_p=0.9,
            num_ctx=2048,
        )
