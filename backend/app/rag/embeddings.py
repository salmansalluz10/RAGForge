"""
EmbeddingService - Abstract embedding provider interface.

Supported Providers:
  - GeminiEmbeddingProvider (Official google-genai SDK, gemini-embedding-001, 768-dim)
  - OpenAIEmbeddingProvider (Official openai SDK, text-embedding-3-small, 1536-dim)
  - MockEmbeddingProvider (Deterministic SHA-256 float vectors for offline/CI testing)
"""
import hashlib
import math
import logging
from abc import ABC, abstractmethod
from typing import List, Optional
from app.core.config import settings

logger = logging.getLogger("ragforge.embeddings")


class BaseEmbeddingProvider(ABC):
    """Abstract base for all embedding providers."""

    @abstractmethod
    def embed_query(self, text: str) -> List[float]:
        """Generate an embedding vector for a single query string."""

    @abstractmethod
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Generate embedding vectors for a list of text chunks."""

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Number of dimensions in the embedding vectors."""


class GeminiEmbeddingProvider(BaseEmbeddingProvider):
    """
    Google Gemini embedding provider using the official google-genai SDK.
    Uses model: gemini-embedding-001 (or configured settings.EMBEDDING_MODEL).
    Output dimensionality: 768 (or configured settings.EMBEDDING_DIMENSIONS).
    Task types:
      - RETRIEVAL_DOCUMENT for indexing document chunks
      - RETRIEVAL_QUERY for user search questions
    """

    def __init__(self, api_key: Optional[str] = None):
        from google import genai
        key = api_key or settings.effective_gemini_api_key
        if not key:
            raise ValueError("Gemini API key is required but not configured.")
        self._client = genai.Client(api_key=key)
        self._model = settings.EMBEDDING_MODEL
        self._dims = settings.EMBEDDING_DIMENSIONS

    def embed_query(self, text: str) -> List[float]:
        """Embed a search query using task_type='RETRIEVAL_QUERY'."""
        from google.genai import types
        if not text or not text.strip():
            raise ValueError("Cannot embed empty query text.")

        cleaned = text.replace("\n", " ").strip()
        try:
            response = self._client.models.embed_content(
                model=self._model,
                contents=cleaned,
                config=types.EmbedContentConfig(
                    task_type="RETRIEVAL_QUERY",
                    output_dimensionality=self._dims,
                ),
            )
            if not response or not response.embeddings:
                raise ValueError("Gemini API returned an empty embedding response.")
            return response.embeddings[0].values
        except Exception as e:
            logger.error(f"Gemini embed_query error: {e}", exc_info=True)
            raise

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed document chunks using task_type='RETRIEVAL_DOCUMENT'."""
        from google.genai import types
        if not texts:
            return []

        cleaned = [t.replace("\n", " ").strip() for t in texts if t and t.strip()]
        if not cleaned:
            return []

        all_embeddings: List[List[float]] = []
        batch_size = 50
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            try:
                response = self._client.models.embed_content(
                    model=self._model,
                    contents=batch,
                    config=types.EmbedContentConfig(
                        task_type="RETRIEVAL_DOCUMENT",
                        output_dimensionality=self._dims,
                    ),
                )
                if not response or not response.embeddings:
                    raise ValueError(f"Gemini API returned empty embeddings for batch starting at index {i}.")
                batch_embeddings = [emb.values for emb in response.embeddings]
                all_embeddings.extend(batch_embeddings)
            except Exception as e:
                logger.error(f"Gemini embed_documents batch error: {e}", exc_info=True)
                raise

        return all_embeddings

    @property
    def dimensions(self) -> int:
        return self._dims


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI text-embedding-3-small / text-embedding-3-large provider."""

    def __init__(self, api_key: Optional[str] = None):
        import openai
        key = api_key or settings.EMBEDDING_API_KEY
        if not key:
            raise ValueError("OpenAI API key is required but not configured.")
        self._client = openai.OpenAI(api_key=key)
        self._model = settings.EMBEDDING_MODEL
        self._dims = settings.EMBEDDING_DIMENSIONS

    def embed_query(self, text: str) -> List[float]:
        text = text.replace("\n", " ").strip()
        response = self._client.embeddings.create(input=[text], model=self._model)
        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        cleaned = [t.replace("\n", " ").strip() for t in texts if t and t.strip()]
        if not cleaned:
            return []
        all_embeddings: List[List[float]] = []
        batch_size = 100
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            batch_embeddings = [item.embedding for item in sorted(response.data, key=lambda x: x.index)]
            all_embeddings.extend(batch_embeddings)
        return all_embeddings

    @property
    def dimensions(self) -> int:
        return self._dims


class MockEmbeddingProvider(BaseEmbeddingProvider):
    """
    Deterministic mock embedding provider for testing and local dev.

    Uses a deterministic hash-based approach:
    - Each unique text always produces the same unit-normalized vector.
    - Semantically different texts produce different (uncorrelated) vectors.
    - No network calls or API keys required.
    """

    def __init__(self, dimensions: Optional[int] = None):
        self._dims = dimensions or settings.EMBEDDING_DIMENSIONS

    def _text_to_vector(self, text: str) -> List[float]:
        """Produce a deterministic unit-normalized float vector from text."""
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        raw = []
        for i in range(0, min(len(digest), self._dims * 2), 2):
            byte_val = int(digest[i : i + 2], 16)
            raw.append((byte_val - 127.5) / 127.5)

        while len(raw) < self._dims:
            raw.extend(raw[: self._dims - len(raw)])

        vec = raw[: self._dims]
        magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / magnitude for x in vec]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts if t and t.strip()]

    @property
    def dimensions(self) -> int:
        return self._dims


class EmbeddingService:
    """
    Singleton embedding service dispatching to the configured provider.
    """

    _instance: Optional["EmbeddingService"] = None

    def __init__(self, provider: BaseEmbeddingProvider):
        self._provider = provider

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = cls._build()
        return cls._instance

    @classmethod
    def reset_instance(cls) -> None:
        """Reset singleton for testing and runtime provider reconfiguration."""
        cls._instance = None

    @classmethod
    def _build(cls) -> "EmbeddingService":
        provider_name = (settings.EMBEDDING_PROVIDER or "").lower()
        gemini_key = settings.effective_gemini_api_key
        openai_key = settings.EMBEDDING_API_KEY or ""

        if provider_name == "gemini":
            if gemini_key:
                try:
                    provider = GeminiEmbeddingProvider(api_key=gemini_key)
                    logger.info(
                        f"Using GeminiEmbeddingProvider with model {settings.EMBEDDING_MODEL} "
                        f"(dimensions={settings.EMBEDDING_DIMENSIONS})"
                    )
                    return cls(provider)
                except Exception as e:
                    logger.error(
                        f"Failed to initialize Gemini embedding provider despite configured key: {e}. "
                        "Falling back to MockEmbeddingProvider.",
                        exc_info=True,
                    )
            else:
                logger.warning(
                    "EMBEDDING_PROVIDER='gemini' is configured, but neither GEMINI_API_KEY nor "
                    "EMBEDDING_API_KEY is set. Falling back to MockEmbeddingProvider."
                )

        elif provider_name == "openai":
            if openai_key:
                try:
                    provider = OpenAIEmbeddingProvider(api_key=openai_key)
                    logger.info(
                        f"Using OpenAIEmbeddingProvider with model {settings.EMBEDDING_MODEL} "
                        f"(dimensions={settings.EMBEDDING_DIMENSIONS})"
                    )
                    return cls(provider)
                except Exception as e:
                    logger.error(
                        f"Failed to initialize OpenAI embedding provider despite configured key: {e}. "
                        "Falling back to MockEmbeddingProvider.",
                        exc_info=True,
                    )
            else:
                logger.warning(
                    "EMBEDDING_PROVIDER='openai' is configured, but EMBEDDING_API_KEY is empty. "
                    "Falling back to MockEmbeddingProvider."
                )
        else:
            logger.warning(
                f"Unknown EMBEDDING_PROVIDER='{provider_name}'. Falling back to MockEmbeddingProvider."
            )

        logger.warning(
            "Using MockEmbeddingProvider - semantic retrieval is disabled. "
            "Configure GEMINI_API_KEY or EMBEDDING_API_KEY to enable real vector search."
        )
        return cls(MockEmbeddingProvider(dimensions=settings.EMBEDDING_DIMENSIONS))

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a search query (RETRIEVAL_QUERY)."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty query text.")
        return self._provider.embed_query(text.strip())

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed document chunks (RETRIEVAL_DOCUMENT)."""
        filtered = [t for t in texts if t and t.strip()]
        if not filtered:
            return []
        return self._provider.embed_documents(filtered)

    @property
    def provider_name(self) -> str:
        return type(self._provider).__name__

    @property
    def dimensions(self) -> int:
        return self._provider.dimensions
