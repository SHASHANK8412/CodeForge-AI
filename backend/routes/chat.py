from __future__ import annotations

import asyncio
import json
from time import perf_counter

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse

from backend.graph.workflow import graph
from backend.memory.conversation_manager import ConversationManager
from backend.memory.crud import generate_conversation_title
from backend.schemas.chat import ChatMessageRequest, ConversationCreateRequest, ConversationRenameRequest


router = APIRouter(prefix="/chat", tags=["chat"])
conversation_manager = ConversationManager()


def _conversation_payload(conversation):
    return {
        "conversation_id": conversation.conversation_id,
        "title": conversation.title,
        "created_at": conversation.created_at,
        "updated_at": conversation.updated_at,
        "last_opened_at": conversation.last_opened_at,
        "message_count": conversation.message_count,
    }


def _message_payload(message):
    return {
        "message_id": message.message_id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "content": message.content,
        "timestamp": message.timestamp,
        "metadata": message.metadata,
    }


@router.post("/new")
def create_conversation(request: ConversationCreateRequest | None = None):
    payload = request or ConversationCreateRequest()
    title = payload.title or (generate_conversation_title(payload.first_message) if payload.first_message else None)
    conversation = conversation_manager.create_conversation(title=title)
    return {
        "success": True,
        "conversation": _conversation_payload(conversation),
    }


@router.post("/message")
async def chat_message(request: ChatMessageRequest):
    started_at = perf_counter()

    if request.conversation_id:
        conversation = conversation_manager.get_conversation(request.conversation_id)
        if conversation is None:
            raise HTTPException(status_code=404, detail="Conversation not found.")
        conversation_id = conversation.conversation_id
    else:
        conversation = conversation_manager.create_conversation(title=generate_conversation_title(request.message))
        conversation_id = conversation.conversation_id

    result = await asyncio.to_thread(
        graph.invoke,
        {
            "prompt": request.message,
            "session_id": conversation_id,
        },
    )

    updated_conversation = conversation_manager.get_conversation(conversation_id)
    messages = conversation_manager.get_messages(conversation_id)

    elapsed_ms = (perf_counter() - started_at) * 1000
    print(f"/chat/message completed in {elapsed_ms:.1f}ms")

    return {
        "success": True,
        "conversation": _conversation_payload(updated_conversation),
        "response": result["response"],
        "plan": result.get("plan", ""),
        "architecture": result.get("architecture", ""),
        "messages": [_message_payload(message) for message in messages],
    }


@router.post("")
async def chat(request: ChatMessageRequest):
    return await chat_message(request)


@router.get("/list")
def list_conversations(
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    search: str | None = Query(default=None, max_length=120),
):
    conversations = conversation_manager.list_conversations(limit=limit, offset=offset, search=search)

    return {
        "success": True,
        "conversations": [_conversation_payload(conversation) for conversation in conversations],
    }


@router.get("/history/{conversation_id}")
def get_conversation_history(conversation_id: str, limit: int = Query(default=100, ge=1, le=500)):
    conversation = conversation_manager.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    messages = conversation_manager.get_messages(conversation_id, limit=limit)
    return {
        "success": True,
        "conversation": _conversation_payload(conversation),
        "messages": [_message_payload(message) for message in messages],
    }


@router.put("/title/{conversation_id}")
def rename_conversation(conversation_id: str, request: ConversationRenameRequest):
    try:
        conversation = conversation_manager.rename_conversation(conversation_id, request.title)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Conversation not found.") from exc

    return {
        "success": True,
        "conversation": _conversation_payload(conversation),
    }


@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    conversation = conversation_manager.get_conversation(conversation_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found.")

    conversation_manager.delete_conversation(conversation_id)
    return {
        "success": True,
        "conversation_id": conversation_id,
    }


@router.post("/stream")
async def chat_stream(request: ChatMessageRequest):
    conversation = conversation_manager.get_conversation(request.conversation_id) if request.conversation_id else None
    conversation_id = conversation.conversation_id if conversation is not None else conversation_manager.create_conversation(title=generate_conversation_title(request.message)).conversation_id
    started_at = perf_counter()
    payload = {
        "prompt": request.message,
        "session_id": conversation_id,
    }

    def event_stream():
        for chunk in graph.stream(payload):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

        elapsed_ms = (perf_counter() - started_at) * 1000
        yield f"data: {json.dumps({'type': 'timing', 'route': 'chat_stream', 'elapsed_ms': round(elapsed_ms, 1)}, ensure_ascii=False)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")