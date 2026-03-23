"""InMail messaging schemas."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional


class ConversationCategory(str, Enum):
    """Category for support conversations."""
    SUPORTE = "suporte"
    SUGESTAO = "sugestao"
    FUNCIONALIDADE = "funcionalidade"
    BUG = "bug"
    OUTRO = "outro"


class ConversationStatus(str, Enum):
    """Status of a support conversation."""
    ABERTO = "aberto"
    RESPONDIDO = "respondido"
    RESOLVIDO = "resolvido"


class CreateConversationRequest(BaseModel):
    """Request to create a new conversation with first message."""
    subject: str = Field(..., min_length=1, max_length=200)
    category: ConversationCategory
    body: str = Field(..., min_length=1, max_length=5000)


class ReplyRequest(BaseModel):
    """Request to reply to a conversation."""
    body: str = Field(..., min_length=1, max_length=5000)


class UpdateConversationStatusRequest(BaseModel):
    """Request to update conversation status (admin only)."""
    status: ConversationStatus


class MessageResponse(BaseModel):
    """Single message in a conversation thread."""
    id: str
    sender_id: str
    sender_email: Optional[str] = None
    body: str
    is_admin_reply: bool
    read_by_user: bool
    read_by_admin: bool
    created_at: str


class ConversationSummary(BaseModel):
    """Summary of a conversation for list views."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    subject: str
    category: str
    status: str
    last_message_at: str
    created_at: str
    unread_count: int = 0


class ConversationDetail(BaseModel):
    """Full conversation with messages thread."""
    id: str
    user_id: str
    user_email: Optional[str] = None
    subject: str
    category: str
    status: str
    last_message_at: str
    created_at: str
    messages: List[MessageResponse] = []


class ConversationsListResponse(BaseModel):
    """Paginated list of conversations."""
    conversations: List[ConversationSummary]
    total: int


class UnreadCountResponse(BaseModel):
    """Unread message count for badge display."""
    unread_count: int


class CreateConversationResponse(BaseModel):
    """Response for POST /api/messages/conversations."""
    id: str
    status: str


class ReplyStatusResponse(BaseModel):
    """Response for POST /api/messages/conversations/{id}/reply."""
    status: str
