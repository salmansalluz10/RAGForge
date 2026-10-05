from typing import List, Dict
from pydantic import BaseModel
from app.schemas.document import DocumentResponse
from app.schemas.chat import ConversationResponse


class DashboardStatsResponse(BaseModel):
    total_documents: int
    total_collections: int
    total_conversations: int
    total_chunks: int
    status_counts: Dict[str, int]
    recent_documents: List[DocumentResponse]
    recent_conversations: List[ConversationResponse]
