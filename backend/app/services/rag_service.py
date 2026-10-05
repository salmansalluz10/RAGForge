import logging
from typing import Optional, List
from sqlalchemy.orm import Session
from app.services.retrieval_service import RetrievalService
from app.rag.llm import LLMService
from app.rag.prompts import RAG_SYSTEM_PROMPT, build_rag_user_prompt
from app.schemas.rag import RAGQueryResponse, SourceCitation

logger = logging.getLogger("ragforge.rag")


class RAGService:
    @staticmethod
    def answer_question(
        db: Session,
        question: str,
        user_id: str,
        collection_id: Optional[str] = None,
        document_ids: Optional[List[str]] = None,
        top_k: Optional[int] = None,
        threshold: Optional[float] = None,
    ) -> RAGQueryResponse:
        """
        Executes end-to-end RAG pipeline:
        1. Semantic vector retrieval of top-K chunks for the user
        2. Construction of structured context
        3. Grounded answer generation via LLM
        4. Structured source citation assembly
        """
        # Step 1: Semantic Retrieval
        context = RetrievalService.retrieve(
            db=db,
            question=question,
            user_id=user_id,
            collection_id=collection_id,
            document_ids=document_ids,
            top_k=top_k,
            threshold=threshold,
        )

        # Step 2: Check if relevant context was found
        if not context.chunks:
            return RAGQueryResponse(
                question=question,
                answer="I could not find enough information in your uploaded documents to answer this question.",
                sources=[],
                chunks_retrieved=0,
            )

        # Step 3: Prompt & LLM Generation
        user_prompt = build_rag_user_prompt(
            question=question,
            context_text=context.context_text,
        )
        llm_service = LLMService.get_instance()
        answer = llm_service.generate(prompt=user_prompt, system_prompt=RAG_SYSTEM_PROMPT)

        # Step 4: Source Citations Assembly
        citations = []
        for chunk in context.chunks:
            snippet = chunk.content[:240].strip() + ("..." if len(chunk.content) > 240 else "")
            citations.append(
                SourceCitation(
                    document_id=chunk.document_id,
                    document_name=chunk.document_name,
                    page_number=chunk.page_number,
                    chunk_index=chunk.chunk_index,
                    score=chunk.score,
                    snippet=snippet,
                )
            )

        return RAGQueryResponse(
            question=question,
            answer=answer,
            sources=citations,
            chunks_retrieved=len(context.chunks),
        )
