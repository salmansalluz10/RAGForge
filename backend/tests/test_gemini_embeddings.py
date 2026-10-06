import pytest
from unittest.mock import MagicMock, patch
from app.core.config import settings
from app.rag.embeddings import (
    GeminiEmbeddingProvider,
    OpenAIEmbeddingProvider,
    MockEmbeddingProvider,
    EmbeddingService,
)


@pytest.fixture(autouse=True)
def reset_service_singleton():
    EmbeddingService.reset_instance()
    yield
    EmbeddingService.reset_instance()


def test_gemini_provider_initialization_with_key():
    """1. Gemini provider initializes successfully with explicit or configured API key."""
    provider = GeminiEmbeddingProvider(api_key="test_gemini_api_key_123")
    assert provider.dimensions == 768
    assert provider._model == "gemini-embedding-001"


def test_gemini_provider_missing_key_raises_value_error():
    """8. Missing Gemini key raises ValueError on direct provider initialization."""
    with patch.object(settings, "GEMINI_API_KEY", ""):
        with patch.object(settings, "EMBEDDING_API_KEY", ""):
            with pytest.raises(ValueError, match="Gemini API key is required"):
                GeminiEmbeddingProvider(api_key="")


def test_gemini_query_embedding_task_type_and_dimension():
    """2, 4, 6. Gemini query embedding uses RETRIEVAL_QUERY, 768-dim, and returns float list."""
    provider = GeminiEmbeddingProvider(api_key="fake_key")

    mock_values = [0.01] * 768
    mock_content_emb = MagicMock()
    mock_content_emb.values = mock_values
    mock_response = MagicMock()
    mock_response.embeddings = [mock_content_emb]

    with patch.object(provider._client.models, "embed_content", return_value=mock_response) as mock_embed:
        result = provider.embed_query("What is the capital of France?")

        assert len(result) == 768
        assert result == mock_values
        mock_embed.assert_called_once()
        _, kwargs = mock_embed.call_args
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["contents"] == "What is the capital of France?"
        assert kwargs["config"].task_type == "RETRIEVAL_QUERY"
        assert kwargs["config"].output_dimensionality == 768


def test_gemini_document_embedding_task_type_and_batching():
    """3, 5, 6. Gemini document embedding uses RETRIEVAL_DOCUMENT, batches, and preserves ordering."""
    provider = GeminiEmbeddingProvider(api_key="fake_key")

    vec1 = [0.1] * 768
    vec2 = [0.2] * 768

    emb1 = MagicMock()
    emb1.values = vec1
    emb2 = MagicMock()
    emb2.values = vec2

    mock_response = MagicMock()
    mock_response.embeddings = [emb1, emb2]

    with patch.object(provider._client.models, "embed_content", return_value=mock_response) as mock_embed:
        docs = ["Section 1: Overview", "Section 2: Architecture"]
        results = provider.embed_documents(docs)

        assert len(results) == 2
        assert results[0] == vec1
        assert results[1] == vec2
        mock_embed.assert_called_once()
        _, kwargs = mock_embed.call_args
        assert kwargs["model"] == "gemini-embedding-001"
        assert kwargs["contents"] == docs
        assert kwargs["config"].task_type == "RETRIEVAL_DOCUMENT"
        assert kwargs["config"].output_dimensionality == 768


def test_gemini_api_error_handling_and_empty_response():
    """9. Gracefully handles API failures and empty embedding payloads."""
    provider = GeminiEmbeddingProvider(api_key="fake_key")

    # API network/rate-limit exception
    with patch.object(provider._client.models, "embed_content", side_effect=RuntimeError("Quota Exceeded")):
        with pytest.raises(RuntimeError, match="Quota Exceeded"):
            provider.embed_query("Sample query")

    # Empty response payload
    empty_response = MagicMock()
    empty_response.embeddings = []
    with patch.object(provider._client.models, "embed_content", return_value=empty_response):
        with pytest.raises(ValueError, match="empty embedding response"):
            provider.embed_query("Sample query")


def test_provider_factory_selects_gemini():
    """7. EmbeddingService selects GeminiEmbeddingProvider when EMBEDDING_PROVIDER=gemini and key exists."""
    with patch.object(settings, "EMBEDDING_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", "real_or_mock_key"):
            service = EmbeddingService._build()
            assert service.provider_name == "GeminiEmbeddingProvider"
            assert service.dimensions == 768


def test_provider_factory_missing_gemini_key_falls_back_to_mock():
    """8, 11. When Gemini key is empty, factory falls back safely to MockEmbeddingProvider."""
    with patch.object(settings, "EMBEDDING_PROVIDER", "gemini"):
        with patch.object(settings, "GEMINI_API_KEY", ""):
            with patch.object(settings, "EMBEDDING_API_KEY", ""):
                service = EmbeddingService._build()
                assert service.provider_name == "MockEmbeddingProvider"
                assert service.dimensions == 768


def test_provider_factory_supports_openai():
    """10. OpenAI provider remains supported when EMBEDDING_PROVIDER=openai and key exists."""
    with patch.object(settings, "EMBEDDING_PROVIDER", "openai"):
        with patch.object(settings, "EMBEDDING_API_KEY", "sk-fake-openai-key"):
            with patch.object(settings, "EMBEDDING_DIMENSIONS", 1536):
                service = EmbeddingService._build()
                assert service.provider_name == "OpenAIEmbeddingProvider"
                assert service.dimensions == 1536


def test_mock_embedding_provider_deterministic():
    """11. MockEmbeddingProvider works deterministically at 768 dimensions without network access."""
    mock_prov = MockEmbeddingProvider(dimensions=768)
    assert mock_prov.dimensions == 768

    v1 = mock_prov.embed_query("Test input text")
    v2 = mock_prov.embed_query("Test input text")
    assert len(v1) == 768
    assert v1 == v2


def test_retrieval_pipeline_with_gemini_service():
    """12. Retrieval service correctly uses the Gemini embedding provider."""
    mock_gemini = MagicMock(spec=GeminiEmbeddingProvider)
    mock_gemini.dimensions = 768
    mock_gemini.embed_query.return_value = [0.05] * 768
    mock_gemini.embed_documents.return_value = [[0.05] * 768]

    svc = EmbeddingService(mock_gemini)
    with patch.object(EmbeddingService, "get_instance", return_value=svc):
        q_vec = svc.embed_query("What is pgvector?")
        assert len(q_vec) == 768
        mock_gemini.embed_query.assert_called_once_with("What is pgvector?")
