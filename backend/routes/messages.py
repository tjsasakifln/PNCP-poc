"""InMail messaging router — threaded support conversations."""

import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from auth import require_auth
from admin import require_admin, _is_admin_from_supabase
from schemas import (
    validate_uuid,
    CreateConversationRequest,
    ReplyRequest,
    UpdateConversationStatusRequest,
    MessageResponse,
    ConversationSummary,
    ConversationDetail,
    ConversationsListResponse,
    UnreadCountResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/messages", tags=["messages"])


def _get_sb():
    from supabase_client import get_supabase
    return get_supabase()


def _is_admin(user_id: str) -> bool:
    """Check admin via env + Supabase (reuses admin.py logic)."""
    from admin import _get_admin_ids
    if user_id.lower() in _get_admin_ids():
        return True
    return _is_admin_from_supabase(user_id)


# --------------------------------------------------------------------------
# 1. POST /api/messages/conversations — create conversation + first message
# --------------------------------------------------------------------------
@router.post("/conversations", status_code=201)
async def create_conversation(
    req: CreateConversationRequest,
    user: dict = Depends(require_auth),
):
    sb = _get_sb()
    user_id = user["id"]

    # Insert conversation
    conv_result = (
        sb.table("conversations")
        .insert({
            "user_id": user_id,
            "subject": req.subject,
            "category": req.category.value,
        })
        .execute()
    )
    if not conv_result.data:
        raise HTTPException(status_code=500, detail="Erro ao criar conversa")

    conv = conv_result.data[0]

    # Insert first message
    sb.table("messages").insert({
        "conversation_id": conv["id"],
        "sender_id": user_id,
        "body": req.body,
        "is_admin_reply": False,
        "read_by_user": True,   # sender already read it
        "read_by_admin": False,
    }).execute()

    logger.info("Conversation %s created by user %s", conv["id"], user_id[:8])
    return {"id": conv["id"], "status": "aberto"}


# --------------------------------------------------------------------------
# 2. GET /api/messages/conversations — list conversations
# --------------------------------------------------------------------------
@router.get("/conversations", response_model=ConversationsListResponse)
async def list_conversations(
    user: dict = Depends(require_auth),
    status: Optional[str] = Query(default=None),
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    sb = _get_sb()
    user_id = user["id"]
    admin = _is_admin(user_id)

    # STORY-202 DB-M06: Use RPC to eliminate N+1 query (one query instead of N+1)
    try:
        result = sb.rpc("get_conversations_with_unread_count", {
            "p_user_id": user_id,
            "p_is_admin": admin,
            "p_status": status,
            "p_limit": limit,
            "p_offset": offset,
        }).execute()

        if not result.data:
            return ConversationsListResponse(conversations=[], total=0)

        # First row contains total_count (same for all rows due to window function)
        total_count = result.data[0]["total_count"] if result.data else 0

        conversations = [
            ConversationSummary(
                id=row["id"],
                user_id=row["user_id"],
                user_email=row["user_email"] if admin else None,
                subject=row["subject"],
                category=row["category"],
                status=row["status"],
                last_message_at=row["last_message_at"],
                created_at=row["created_at"],
                unread_count=row["unread_count"],
            )
            for row in result.data
        ]

        return ConversationsListResponse(
            conversations=conversations,
            total=total_count,
        )

    except Exception as e:
        logger.error(f"Error calling get_conversations_with_unread_count RPC: {e}")
        # Fallback to empty list on RPC error (graceful degradation)
        return ConversationsListResponse(conversations=[], total=0)


# --------------------------------------------------------------------------
# 3. GET /api/messages/conversations/{id} — get thread + mark read
# --------------------------------------------------------------------------
@router.get("/conversations/{conversation_id}", response_model=ConversationDetail)
async def get_conversation(
    conversation_id: str,
    user: dict = Depends(require_auth),
):
    try:
        conversation_id = validate_uuid(conversation_id, "conversation_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de conversa invalido")

    sb = _get_sb()
    user_id = user["id"]
    admin = _is_admin(user_id)

    # Fetch conversation
    conv_result = (
        sb.table("conversations")
        .select("*, profiles!conversations_user_id_fkey(email)")
        .eq("id", conversation_id)
        .single()
        .execute()
    )
    if not conv_result.data:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")

    conv = conv_result.data

    # Authorization check
    if not admin and conv["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Fetch messages
    msgs_result = (
        sb.table("messages")
        .select("*, profiles!messages_sender_id_fkey(email)")
        .eq("conversation_id", conversation_id)
        .order("created_at", desc=False)
        .execute()
    )

    # Mark messages as read
    if admin:
        # Admin reading: mark user messages as read_by_admin
        sb.table("messages").update({"read_by_admin": True}).eq(
            "conversation_id", conversation_id
        ).eq("is_admin_reply", False).eq("read_by_admin", False).execute()
    else:
        # User reading: mark admin replies as read_by_user
        sb.table("messages").update({"read_by_user": True}).eq(
            "conversation_id", conversation_id
        ).eq("is_admin_reply", True).eq("read_by_user", False).execute()

    profile_data = conv.get("profiles") or {}
    messages = []
    for m in msgs_result.data or []:
        sender_profile = m.get("profiles") or {}
        messages.append(MessageResponse(
            id=m["id"],
            sender_id=m["sender_id"],
            sender_email=sender_profile.get("email"),
            body=m["body"],
            is_admin_reply=m["is_admin_reply"],
            read_by_user=m["read_by_user"],
            read_by_admin=m["read_by_admin"],
            created_at=m["created_at"],
        ))

    return ConversationDetail(
        id=conv["id"],
        user_id=conv["user_id"],
        user_email=profile_data.get("email") if admin else None,
        subject=conv["subject"],
        category=conv["category"],
        status=conv["status"],
        last_message_at=conv["last_message_at"],
        created_at=conv["created_at"],
        messages=messages,
    )


# --------------------------------------------------------------------------
# 4. POST /api/messages/conversations/{id}/reply — reply to thread
# --------------------------------------------------------------------------
@router.post("/conversations/{conversation_id}/reply", status_code=201)
async def reply_to_conversation(
    conversation_id: str,
    req: ReplyRequest,
    user: dict = Depends(require_auth),
):
    try:
        conversation_id = validate_uuid(conversation_id, "conversation_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de conversa invalido")

    sb = _get_sb()
    user_id = user["id"]
    admin = _is_admin(user_id)

    # Verify conversation exists and user has access
    conv_result = (
        sb.table("conversations")
        .select("id, user_id, status")
        .eq("id", conversation_id)
        .single()
        .execute()
    )
    if not conv_result.data:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")

    conv = conv_result.data
    if not admin and conv["user_id"] != user_id:
        raise HTTPException(status_code=403, detail="Acesso negado")

    # Insert message
    sb.table("messages").insert({
        "conversation_id": conversation_id,
        "sender_id": user_id,
        "body": req.body,
        "is_admin_reply": admin,
        "read_by_user": not admin,   # if admin replies, user hasn't read yet
        "read_by_admin": admin,      # if user replies, admin hasn't read yet
    }).execute()

    # Auto-transition status
    new_status = "respondido" if admin else "aberto"
    if conv["status"] != "resolvido":
        sb.table("conversations").update({"status": new_status}).eq(
            "id", conversation_id
        ).execute()

    logger.info(
        "Reply to conversation %s by %s (admin=%s)",
        conversation_id[:8], user_id[:8], admin,
    )
    return {"status": new_status}


# --------------------------------------------------------------------------
# 5. PATCH /api/messages/conversations/{id}/status — admin set status
# --------------------------------------------------------------------------
@router.patch("/conversations/{conversation_id}/status")
async def update_conversation_status(
    conversation_id: str,
    req: UpdateConversationStatusRequest,
    admin: dict = Depends(require_admin),
):
    try:
        conversation_id = validate_uuid(conversation_id, "conversation_id")
    except ValueError:
        raise HTTPException(status_code=400, detail="ID de conversa invalido")

    sb = _get_sb()

    result = (
        sb.table("conversations")
        .update({"status": req.status.value})
        .eq("id", conversation_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=404, detail="Conversa nao encontrada")

    logger.info(
        "Conversation %s status changed to %s by admin %s",
        conversation_id[:8], req.status.value, admin["id"][:8],
    )
    return {"status": req.status.value}


# --------------------------------------------------------------------------
# 6. GET /api/messages/unread-count — badge count
# --------------------------------------------------------------------------
@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(
    user: dict = Depends(require_auth),
):
    sb = _get_sb()
    user_id = user["id"]
    admin = _is_admin(user_id)

    if admin:
        # Admin: count user messages not read by admin, across ALL conversations
        result = (
            sb.table("messages")
            .select("id", count="exact")
            .eq("is_admin_reply", False)
            .eq("read_by_admin", False)
            .execute()
        )
    else:
        # User: count admin replies not read by user, in own conversations only
        # First get own conversation IDs
        convs = (
            sb.table("conversations")
            .select("id")
            .eq("user_id", user_id)
            .execute()
        )
        conv_ids = [c["id"] for c in (convs.data or [])]
        if not conv_ids:
            return UnreadCountResponse(unread_count=0)

        result = (
            sb.table("messages")
            .select("id", count="exact")
            .in_("conversation_id", conv_ids)
            .eq("is_admin_reply", True)
            .eq("read_by_user", False)
            .execute()
        )

    return UnreadCountResponse(unread_count=result.count or 0)
