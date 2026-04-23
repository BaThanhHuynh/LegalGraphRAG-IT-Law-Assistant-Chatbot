from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    message: str = Field(..., description="Câu hỏi của người dùng")
    conversation_id: Optional[str] = Field(None, description="ID cuộc hội thoại nếu đã có")

class Source(BaseModel):
    article: str
    content: str
    score: float
    doc_title: str

class ChatResponseData(BaseModel):
    conversation_id: str
    answer: str
    sources: List[Source]
    graph_data: Dict[str, Any]

class ChatResponse(BaseModel):
    success: bool
    data: ChatResponseData

class ConversationItem(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class ConversationListResponse(BaseModel):
    success: bool
    data: List[ConversationItem]

class NewConversationResponse(BaseModel):
    success: bool
    data: Dict[str, str]

class HistoryResponse(BaseModel):
    success: bool
    data: List[Dict[str, Any]]

class KGResponse(BaseModel):
    success: bool
    data: Dict[str, Any]
