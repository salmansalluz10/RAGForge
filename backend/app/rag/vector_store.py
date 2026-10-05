"""
VectorStore - pgvector-backed semantic similarity search.

Design:
  - PostgreSQL: uses native cosine distance (<=> operator from pgvector).
  - SQLite (dev/test): performs cosine similarity in pure Python since
    SQLite has no vector type.
  - User isolation is enforced at the JOIN level — users never see
    each other's embeddings.
"""
import json
import math
import logging
from typing import List, Optional
from dataclasses import dataclass
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.core.config import settings
from app.models.document import Document, DocumentChunk

logger = logging.getLogger("ragforge.vectorstore")


@dataclass
class SearchResult:
    chunk_id: str
    document_id: str
    document_name: str
    chunk_index: int
    content: str
    page_number: Optional[int]
    score: float  # Higher = more similar
    chunk_metadata: Optional[dict]


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """Pure-Python cosine similarity between two L2-normalized vectors."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a)) or 1.0
    mag_b = math.sqrt(sum(x * x for x in b)) or 1.0
    return dot / (mag_a * mag_b)


class VectorStore:
    """
    Handles embedding storage and semantic retrieval against pgvector or SQLite.
    """

    @staticmethod
    def is_postgresql(db: Session) -> bool:
        return "postgresql" in str(db.bind.url)

    @staticmethod
    def store_embedding(db: Session, chunk_id: str, embedding: List[float]) -> None:
        """Store or update the embedding for a document chunk."""
        chunk = db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).first()
        if chunk:
            chunk.embedding = embedding
            db.add(chunk)

    @staticmethod
    def store_embeddings_batch(
        db: Session,
        chunk_embedding_pairs: List[tuple],
    ) -> None:
        """
        Batch update embeddings for multiple chunks.
        chunk_embedding_pairs: list of (chunk_id, embedding_vector)
        """
        for chunk_id, embedding in chunk_embedding_pairs:
            db.query(DocumentChunk).filter(DocumentChunk.id == chunk_id).update(
                {"embedding": embedding},
                synchronize_session=False,
            )
        db.commit()

    @staticmethod
    def similarity_search(
        db: Session,
        query_embedding: List[float],
        user_id: str,
        top_k: Optional[int] = None,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        threshold: Optional[float] = None,
    ) -> List[SearchResult]:
        """
        Perform semantic similarity search.

        Enforces user-level isolation: only chunks belonging to the
        authenticated user's documents are searched.
        """
        k = top_k or settings.TOP_K
        min_score = threshold if threshold is not None else settings.SIMILARITY_THRESHOLD

        dialect = db.bind.dialect.name

        if dialect == "postgresql":
            return VectorStore._pg_similarity_search(
                db, query_embedding, user_id, k, collection_id, document_ids, min_score
            )
        else:
            return VectorStore._sqlite_similarity_search(
                db, query_embedding, user_id, k, collection_id, document_ids, min_score
            )

    @staticmethod
    def _pg_similarity_search(
        db: Session,
        query_embedding: List[float],
        user_id: str,
        top_k: int,
        collection_id: Optional[str],
        document_ids: Optional[List[str]],
        threshold: float,
    ) -> List[SearchResult]:
        """
        Uses pgvector's <=> (cosine distance) operator.
        Cosine distance = 1 - cosine_similarity, so lower distance = better match.
        """
        vector_literal = f"[{','.join(str(v) for v in query_embedding)}]"

        conditions = [
            "d.user_id = :user_id",
            "dc.embedding IS NOT NULL",
            "d.processing_status = 'COMPLETED'",
        ]
        params: dict = {"user_id": user_id, "top_k": top_k, "threshold": 1.0 - threshold}

        if collection_id:
            conditions.append("d.collection_id = :collection_id")
            params["collection_id"] = collection_id
        if document_ids:
            conditions.append("d.id = ANY(:doc_ids)")
            params["doc_ids"] = document_ids

        where_clause = " AND ".join(conditions)

        sql = text(f"""
            SELECT
                dc.id          AS chunk_id,
                dc.document_id,
                d.original_filename AS document_name,
                dc.chunk_index,
                dc.content,
                dc.chunk_metadata,
                (dc.embedding <=> '{vector_literal}'::vector) AS distance
            FROM document_chunks dc
            JOIN documents d ON d.id = dc.document_id
            WHERE {where_clause}
              AND (dc.embedding <=> '{vector_literal}'::vector) < :threshold
            ORDER BY distance ASC
            LIMIT :top_k
        """)

        rows = db.execute(sql, params).mappings().all()
        results = []
        for row in rows:
            meta = row["chunk_metadata"] or {}
            if isinstance(meta, str):
                try:
                    meta = json.loads(meta)
                except Exception:
                    meta = {}
            results.append(SearchResult(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                document_name=row["document_name"],
                chunk_index=row["chunk_index"],
                content=row["content"],
                page_number=meta.get("page_number"),
                score=round(1.0 - float(row["distance"]), 4),
                chunk_metadata=meta,
            ))
        return results

    @staticmethod
    def _sqlite_similarity_search(
        db: Session,
        query_embedding: List[float],
        user_id: str,
        top_k: int,
        collection_id: Optional[str],
        document_ids: Optional[List[str]],
        threshold: float,
    ) -> List[SearchResult]:
        """
        Pure-Python cosine similarity search for SQLite (dev/test).
        Loads all chunks from user's documents into memory and computes similarity.
        """
        query = (
            db.query(DocumentChunk, Document)
            .join(Document, Document.id == DocumentChunk.document_id)
            .filter(
                Document.user_id == user_id,
                Document.processing_status == "COMPLETED",
                DocumentChunk.embedding.isnot(None),
            )
        )
        if collection_id:
            query = query.filter(Document.collection_id == collection_id)
        if document_ids:
            query = query.filter(Document.id.in_(document_ids))

        rows = query.all()
        scored = []

        for chunk, doc in rows:
            emb = chunk.embedding
            if isinstance(emb, str):
                try:
                    emb = json.loads(emb)
                except Exception:
                    continue
            if not emb or not isinstance(emb, list):
                continue

            score = _cosine_similarity(query_embedding, emb)
            if score >= threshold:
                meta = chunk.chunk_metadata or {}
                if isinstance(meta, str):
                    try:
                        meta = json.loads(meta)
                    except Exception:
                        meta = {}
                scored.append((score, chunk, doc, meta))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [
            SearchResult(
                chunk_id=chunk.id,
                document_id=chunk.document_id,
                document_name=doc.original_filename,
                chunk_index=chunk.chunk_index,
                content=chunk.content,
                page_number=meta.get("page_number"),
                score=round(score, 4),
                chunk_metadata=meta,
            )
            for score, chunk, doc, meta in scored[:top_k]
        ]
