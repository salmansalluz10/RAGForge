"""
RetrievalService - Semantic search and context construction for RAG.

Pipeline:
  User Question
    → Question Embedding (EmbeddingService)
    → Cosine Similarity Search (VectorStore / pgvector)
    → Top-K Ranked Chunks (user-isolated)
    → Structured Context + Source Citations
"""
import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from dataclasses import dataclass
from app.rag.embeddings import EmbeddingService
from app.rag.vector_store import VectorStore, SearchResult
from app.core.config import settings

logger = logging.getLogger("ragforge.retrieval")


@dataclass
class RetrievedContext:
    """Structured retrieval result passed to the LLM."""
    chunks: List[SearchResult]
    context_text: str
    sources: List[dict]


class RetrievalService:

    @staticmethod
    def retrieve(
        db: Session,
        question: str,
        user_id: str,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> RetrievedContext:
        """
        Embed the question, search for the most relevant chunks, and
        construct a formatted context block with citations.
        """
        if not question or not question.strip():
            raise ValueError("Search query cannot be empty.")

        # 1. Embed the user's question
        embedding_service = EmbeddingService.get_instance()
        try:
            query_vector = embedding_service.embed_query(question)
        except Exception as e:
            logger.error(f"Failed to embed query: {e}")
            raise RuntimeError(f"Failed to generate query embedding: {str(e)}")

        # 2. Run vector similarity search with user isolation
        try:
            results = VectorStore.similarity_search(
                db=db,
                query_embedding=query_vector,
                user_id=user_id,
                top_k=top_k or settings.TOP_K,
                collection_id=collection_id,
                document_ids=document_ids,
                threshold=threshold,
            )
        except Exception as e:
            logger.error(f"Vector search error: {e}")
            raise RuntimeError(f"Similarity search failed: {str(e)}")

        logger.info(f"Retrieved {len(results)} chunks for user {user_id}")

        # 3. Build formatted context block for LLM prompt
        context_parts = []
        sources = []
        seen_sources = set()

        for idx, result in enumerate(results):
            context_parts.append(
                f"[Source {idx + 1}] {result.document_name}"
                + (f" — Page {result.page_number}" if result.page_number else "")
                + f"\n{result.content}"
            )

            source_key = f"{result.document_id}:{result.page_number}"
            if source_key not in seen_sources:
                seen_sources.add(source_key)
                sources.append({
                    "document_id": result.document_id,
                    "document_name": result.document_name,
                    "page_number": result.page_number,
                    "chunk_index": result.chunk_index,
                    "score": result.score,
                })

        context_text = "\n\n---\n\n".join(context_parts) if context_parts else ""

        return RetrievedContext(
            chunks=results,
            context_text=context_text,
            sources=sources,
        )
