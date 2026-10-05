"""
EmbeddingService - Abstract embedding provider interface.

Design decision:
  - Clean abstraction so the provider (OpenAI, HuggingFace, local, etc.)
    can be swapped via environment variables without touching RAG logic.
  - In testing/dev without an API key, a deterministic random-seed fallback
    is used so tests don't require network access.
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


class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    """OpenAI text-embedding-3-small / text-embedding-3-large provider."""

    def __init__(self):
        import openai
        self._client = openai.OpenAI(api_key=settings.EMBEDDING_API_KEY)
        self._model = settings.EMBEDDING_MODEL
        self._dims = settings.EMBEDDING_DIMENSIONS

    def embed_query(self, text: str) -> List[float]:
        text = text.replace("\n", " ").strip()
        response = self._client.embeddings.create(input=[text], model=self._model)
        return response.data[0].embedding

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        cleaned = [t.replace("\n", " ").strip() for t in texts]
        # OpenAI supports batch embedding up to 2048 tokens per string
        all_embeddings: List[List[float]] = []
        batch_size = 100
        for i in range(0, len(cleaned), batch_size):
            batch = cleaned[i : i + batch_size]
            response = self._client.embeddings.create(input=batch, model=self._model)
            # Results are returned in order
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
    - Each unique text always produces the same vector.
    - Semantically different texts produce different (uncorrelated) vectors.
    - No network calls required.

    WARNING: Similarity search results will be meaningless with mock embeddings.
    Set EMBEDDING_API_KEY in production to use real embeddings.
    """

    def __init__(self, dimensions: Optional[int] = None):
        self._dims = dimensions or settings.EMBEDDING_DIMENSIONS

    def _text_to_vector(self, text: str) -> List[float]:
        """Produce a deterministic unit-normalized float vector from text."""
        # Use SHA256 hash as a reproducible seed source
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        # Convert hex pairs into floats in range [-1, 1]
        raw = []
        for i in range(0, min(len(digest), self._dims * 2), 2):
            byte_val = int(digest[i : i + 2], 16)
            raw.append((byte_val - 127.5) / 127.5)

        # Pad if needed by cycling through the raw values
        while len(raw) < self._dims:
            raw.extend(raw[: self._dims - len(raw)])

        vec = raw[: self._dims]

        # L2 normalize the vector
        magnitude = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / magnitude for x in vec]

    def embed_query(self, text: str) -> List[float]:
        return self._text_to_vector(text)

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._text_to_vector(t) for t in texts]

    @property
    def dimensions(self) -> int:
        return self._dims


class EmbeddingService:
    """
    Singleton-pattern embedding service.

    Usage:
        embedding_svc = EmbeddingService.get_instance()
        vector = embedding_svc.embed_query("What is the revenue?")
        vectors = embedding_svc.embed_documents(["chunk 1 text", "chunk 2 text"])
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
        """Reset singleton for testing purposes."""
        cls._instance = None

    @classmethod
    def _build(cls) -> "EmbeddingService":
        provider_name = (settings.EMBEDDING_PROVIDER or "").lower()
        api_key = settings.EMBEDDING_API_KEY or ""

        if provider_name == "openai" and api_key:
            try:
                provider = OpenAIEmbeddingProvider()
                logger.info(f"Embedding provider: OpenAI ({settings.EMBEDDING_MODEL})")
                return cls(provider)
            except Exception as e:
                logger.warning(f"Failed to initialize OpenAI embedding provider: {e}. Falling back to mock.")

        logger.warning(
            "Using MockEmbeddingProvider - similarity search will not be semantically meaningful. "
            "Set EMBEDDING_API_KEY to enable real embeddings."
        )
        return cls(MockEmbeddingProvider())

    def embed_query(self, text: str) -> List[float]:
        """Generate embedding for a search query."""
        if not text or not text.strip():
            raise ValueError("Cannot embed empty text.")
        return self._provider.embed_query(text.strip())

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Batch embed multiple text chunks."""
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
