"""Tests for LLM providers."""

from unittest.mock import MagicMock, patch

import pytest

from quantchain.core.llm_providers import (
    AnthropicProvider,
    LLMResponse,
    OllamaProvider,
    OpenAIProvider,
    VLLMProvider,
    create_llm_provider,
)


@pytest.mark.unit
class TestLLMResponse:
    """Test LLMResponse dataclass."""

    def test_llm_response_creation(self) -> None:
        """Test creating an LLMResponse."""
        response = LLMResponse(
            text="Test response", usage={"tokens": 10}, finish_reason="stop"
        )
        assert response.text == "Test response"
        assert response.usage == {"tokens": 10}
        assert response.finish_reason == "stop"

    def test_llm_response_defaults(self) -> None:
        """Test LLMResponse with defaults."""
        response = LLMResponse(text="Test")
        assert response.usage is None
        assert response.finish_reason is None


@pytest.mark.unit
class TestOpenAIProvider:
    """Test OpenAI provider."""

    def test_openai_provider_init_missing_package(self) -> None:
        """Test OpenAI provider initialization when package is not installed."""
        # Temporarily set OpenAI to None to simulate missing package
        import quantchain.core.llm_providers as providers_module

        original_openai = providers_module.OpenAI
        providers_module.OpenAI = None

        try:
            with pytest.raises(ImportError, match="OpenAI package not installed"):
                OpenAIProvider()
        finally:
            # Restore original value
            providers_module.OpenAI = original_openai

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_init_success(self, mock_openai) -> None:
        """Test successful OpenAI provider initialization."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = OpenAIProvider()

        assert provider.api_key == "test-key"
        assert provider.model == "gpt-4"
        mock_openai.assert_called_once_with(api_key="test-key")

    def test_openai_provider_init_no_key(self) -> None:
        """Test OpenAI provider initialization without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="OpenAI API key required"):
                OpenAIProvider()

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_generate(self, mock_openai) -> None:
        """Test OpenAI provider generate method."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices: list[float] = [MagicMock()]
        mock_response.choices[0].message.content = "Generated text"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage.model_dump.return_value = {"tokens": 10}
        mock_client.chat.completions.create.return_value = mock_response

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = OpenAIProvider()

        response = provider.generate("Test prompt")

        assert isinstance(response, LLMResponse)
        assert response.text == "Generated text"
        assert response.finish_reason == "stop"
        assert response.usage == {"tokens": 10}

    @patch("quantchain.core.llm_providers.OpenAI")
    def test_openai_provider_get_model_name(self, mock_openai) -> None:
        """Test OpenAI provider get_model_name."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            provider = OpenAIProvider(model="gpt-3.5-turbo")

        assert provider.get_model_name() == "gpt-3.5-turbo"


@pytest.mark.unit
class TestAnthropicProvider:
    """Test Anthropic provider."""

    def test_anthropic_provider_init_missing_package(self) -> None:
        """Test Anthropic provider initialization when package is not installed."""
        # Temporarily set anthropic to None to simulate missing package
        import quantchain.core.llm_providers as providers_module

        original_anthropic = providers_module.anthropic
        providers_module.anthropic = None

        try:
            with pytest.raises(ImportError, match="Anthropic package not installed"):
                AnthropicProvider()
        finally:
            # Restore original value
            providers_module.anthropic = original_anthropic

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_init_success(self, mock_anthropic) -> None:
        """Test successful Anthropic provider initialization."""
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = AnthropicProvider()

        assert provider.api_key == "test-key"
        assert provider.model == "claude-3-sonnet-20240229"
        mock_anthropic.Anthropic.assert_called_once_with(api_key="test-key")

    def test_anthropic_provider_init_no_key(self) -> None:
        """Test Anthropic provider initialization without API key."""
        with patch("quantchain.core.llm_providers.anthropic") as mock_anthropic:
            mock_anthropic.Anthropic.return_value = MagicMock()
            with pytest.raises(ValueError, match="Anthropic API key required"):
                AnthropicProvider()

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_generate(self, mock_anthropic) -> None:
        """Test Anthropic provider generate method."""
        mock_client = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content: list[float] = [MagicMock()]
        mock_response.content[0].text = "Generated text"
        mock_response.stop_reason = "end_turn"
        mock_response.usage.input_tokens = 5
        mock_response.usage.output_tokens = 5
        mock_client.messages.create.return_value = mock_response

        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = AnthropicProvider()

        response = provider.generate("Test prompt")

        assert isinstance(response, LLMResponse)
        assert response.text == "Generated text"
        assert response.finish_reason == "end_turn"
        assert response.usage == {"input_tokens": 5, "output_tokens": 5}

    @patch("quantchain.core.llm_providers.anthropic")
    def test_anthropic_provider_get_model_name(self, mock_anthropic) -> None:
        """Test Anthropic provider get_model_name."""
        with patch.dict("os.environ", {"ANTHROPIC_API_KEY": "test-key"}):
            provider = AnthropicProvider(model="claude-3-haiku")

        assert provider.get_model_name() == "claude-3-haiku"


@pytest.mark.unit
class TestOllamaProvider:
    """Test Ollama provider."""

    def test_ollama_provider_init_missing_package(self) -> None:
        """Test Ollama provider initialization when package is not installed."""
        # Temporarily set ollama to None to simulate missing package
        import quantchain.core.llm_providers as providers_module

        original_ollama = providers_module.ollama
        providers_module.ollama = None

        try:
            with pytest.raises(ImportError, match="Ollama package not installed"):
                OllamaProvider()
        finally:
            # Restore original value
            providers_module.ollama = original_ollama

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_init_success(self, mock_ollama) -> None:
        """Test successful Ollama provider initialization."""
        provider = OllamaProvider()

        assert provider.model == "llama2:7b"
        assert provider.host == "http://localhost:11434"

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_generate(self, mock_ollama) -> None:
        """Test Ollama provider generate method."""
        mock_response = {
            "message": {"content": "Generated text"},
            "done_reason": "stop",
        }
        mock_ollama.chat.return_value = mock_response

        provider = OllamaProvider()
        response = provider.generate("Test prompt")

        assert isinstance(response, LLMResponse)
        assert response.text == "Generated text"
        assert response.finish_reason == "stop"

    @patch("quantchain.core.llm_providers.ollama")
    def test_ollama_provider_get_model_name(self, mock_ollama) -> None:
        """Test Ollama provider get_model_name."""
        provider = OllamaProvider(model="codellama:13b")

        assert provider.get_model_name() == "codellama:13b"


@pytest.mark.unit
class TestVLLMProvider:
    """Test VLLM provider."""

    def test_vllm_provider_init_raises(self) -> None:
        """Test VLLM provider initialization raises appropriate error."""
        # Handle both scenarios: vLLM not available (ImportError) or available but not implemented (NotImplementedError)
        with pytest.raises((ImportError, NotImplementedError)) as exc_info:
            VLLMProvider("test-model")

        # Check if it's the expected error for either case
        if isinstance(exc_info.value, ImportError):
            assert "vLLM package not installed" in str(exc_info.value)
        else:
            assert "vLLM provider not yet implemented" in str(exc_info.value)

    def test_vllm_provider_generate_raises(self) -> None:
        """Test VLLM provider generate raises NotImplementedError."""
        provider = VLLMProvider.__new__(VLLMProvider)  # Create without __init__
        with pytest.raises(NotImplementedError):
            provider.generate("test")

    def test_vllm_provider_get_model_name(self) -> None:
        """Test VLLM provider get_model_name."""
        provider = VLLMProvider.__new__(VLLMProvider)  # Create without __init__
        provider.model_name = "test-model"
        assert provider.get_model_name() == "test-model"


@pytest.mark.unit
class TestCreateLLMProvider:
    """Test create_llm_provider function."""

    @patch("quantchain.core.llm_providers.OpenAIProvider")
    def test_create_openai_provider(self, mock_provider) -> None:
        """Test creating OpenAI provider."""
        create_llm_provider("openai", api_key="test")
        mock_provider.assert_called_once_with(api_key="test")

    @patch("quantchain.core.llm_providers.AnthropicProvider")
    def test_create_anthropic_provider(self, mock_provider) -> None:
        """Test creating Anthropic provider."""
        create_llm_provider("anthropic", api_key="test")
        mock_provider.assert_called_once_with(api_key="test")

    @patch("quantchain.core.llm_providers.OllamaProvider")
    def test_create_ollama_provider(self, mock_provider) -> None:
        """Test creating Ollama provider."""
        create_llm_provider("ollama", model="test-model")
        mock_provider.assert_called_once_with(model="test-model")

    def test_create_unknown_provider(self) -> None:
        """Test creating unknown provider raises ValueError."""
        with pytest.raises(ValueError, match="Unsupported provider"):
            create_llm_provider("unknown")
