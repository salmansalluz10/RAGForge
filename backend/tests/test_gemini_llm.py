import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.rag.llm import (
    GeminiLLMProvider,
    OpenAILLMProvider,
    MockLLMProvider,
    LLMService,
)


@pytest.fixture(autouse=True)
def reset_service_singleton():
    LLMService.reset_instance()
    yield
    LLMService.reset_instance()


def test_gemini_llm_initialization_with_key():
    """Gemini LLM provider initializes with explicit or configured key."""
    provider = GeminiLLMProvider(api_key="fake_gemini_key_123")
    assert provider._model == "gemini-2.5-flash"
    assert provider._temperature == 0.2


def test_gemini_llm_missing_key_raises_error():
    """Missing key raises ValueError on GeminiLLMProvider initialization."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with patch.object(settings, "EMBEDDING_API_KEY", ""):
            with patch.object(settings, "LLM_API_KEY", ""):
                with pytest.raises(ValueError, match="Gemini API key is required"):
                    GeminiLLMProvider(api_key="")


def test_gemini_llm_generate_response_mocked():
    """Gemini LLM provider calls generate_content with system prompt and user prompt."""
    provider = GeminiLLMProvider(api_key="fake_key")

    mock_response = MagicMock()
    mock_response.text = "This is a grounded answer from Gemini."

    with patch.object(provider._client.models, "generate_content", return_value=mock_response) as mock_gen:
        answer = provider.generate_response(
            prompt="What is RAG?",
            system_prompt="Answer strictly from context."
        )

        assert answer == "This is a grounded answer from Gemini."
        mock_gen.assert_called_once()
        _, kwargs = mock_gen.call_args
        assert kwargs["model"] == "gemini-2.5-flash"
        assert kwargs["contents"] == "What is RAG?"
        assert kwargs["config"].system_instruction == "Answer strictly from context."


def test_gemini_llm_api_error_handling():
    """Gemini LLM provider raises and logs on API failures."""
    provider = GeminiLLMProvider(api_key="fake_key")

    with patch.object(provider._client.models, "generate_content", side_effect=RuntimeError("Quota Exceeded")):
        with pytest.raises(RuntimeError, match="Quota Exceeded"):
            provider.generate_response("Question", "System Prompt")


def test_llm_factory_selects_gemini():
    """LLMService factory selects GeminiLLMProvider when LLM_PROVIDER=gemini and key is present."""
    with patch.object(settings, "LLM_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", "real_or_mock_key"):
            service = LLMService._build()
            assert service.provider_name == "GeminiLLMProvider"


def test_llm_factory_fails_clearly_when_gemini_key_missing():
    """LLMService factory fails clearly and does NOT silently select MockLLMProvider when key is missing."""
    with patch.object(settings, "LLM_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            with patch.object(settings, "EMBEDDING_API_KEY", ""):
                with patch.object(settings, "LLM_API_KEY", ""):
                    with pytest.raises(ValueError, match="LLM_PROVIDER='gemini' is configured, but neither GEMINI_API_KEY nor EMBEDDING_API_KEY is set"):
                        LLMService._build()


def test_llm_factory_selects_openai():
    """LLMService factory selects OpenAILLMProvider when LLM_PROVIDER=openai and key is present."""
    with patch.object(settings, "LLM_PROVIDER", "openai"):
        with patch.object(settings, "LLM_API_KEY", "sk-fake-openai-key"):
            service = LLMService._build()
            assert service.provider_name == "OpenAILLMProvider"


def test_llm_factory_fails_clearly_when_openai_key_missing():
    """LLMService factory fails clearly when OpenAI key is missing."""
    with patch.object(settings, "LLM_PROVIDER", "openai"):
        with patch.object(settings, "LLM_API_KEY", ""):
            with pytest.raises(ValueError, match="LLM_PROVIDER='openai' is configured, but LLM_API_KEY is empty"):
                LLMService._build()


def test_llm_factory_selects_mock_only_when_explicitly_configured():
    """MockLLMProvider is ONLY selected when LLM_PROVIDER=mock is explicitly set."""
    with patch.object(settings, "LLM_PROVIDER", "mock"):
        service = LLMService._build()
        assert service.provider_name == "MockLLMProvider"
