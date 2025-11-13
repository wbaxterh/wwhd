"""Chat API endpoints with streaming support"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List, AsyncGenerator
import json
import time
import logging

from models import get_db, User, Chat, Message
from schemas.chat import (
    MessageCreate, MessageResponse, ChatCreate,
    ChatResponse, ChatListResponse, CompletionRequest
)
from api.auth import get_current_user
from agents.orchestrator import OrchestratorAgent
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from config import settings

router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize orchestrator lazily to avoid startup issues
orchestrator = None

def get_orchestrator():
    """Get or create orchestrator instance"""
    global orchestrator
    if orchestrator is None:
        orchestrator = OrchestratorAgent()
    return orchestrator


@router.post("/chat", response_model=MessageResponse)
async def create_message(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a new message and get AI response"""
    start_time = time.time()

    # Get or create chat
    if message_data.chat_id:
        result = await db.execute(
            select(Chat).where(
                Chat.id == message_data.chat_id,
                Chat.user_id == current_user.id
            )
        )
        chat = result.scalar_one_or_none()
        if not chat:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Chat not found"
            )
    else:
        # Create new chat
        chat = Chat(
            user_id=current_user.id,
            title=message_data.content[:50] + "..." if len(message_data.content) > 50 else message_data.content
        )
        db.add(chat)
        await db.commit()
        await db.refresh(chat)

    # Save user message
    user_message = Message(
        chat_id=chat.id,
        user_id=current_user.id,
        role="user",
        content=message_data.content
    )
    db.add(user_message)
    await db.commit()

    # Get chat history
    result = await db.execute(
        select(Message).where(Message.chat_id == chat.id).order_by(Message.created_at)
    )
    messages = result.scalars().all()

    # Convert to LangChain messages
    chat_history = []
    for msg in messages[:-1]:  # Exclude the current message
        if msg.role == "user":
            chat_history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            chat_history.append(AIMessage(content=msg.content))

    try:
        # Process with orchestrator
        response = await get_orchestrator().process(
            query=message_data.content,
            chat_history=chat_history
        )

        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)

        # Save assistant message
        assistant_message = Message(
            chat_id=chat.id,
            user_id=current_user.id,
            role="assistant",
            content=response["content"],
            agent_used=", ".join(response.get("agents_used", [])),
            sources_json=response.get("sources", []),
            response_time_ms=response_time_ms
        )
        db.add(assistant_message)
        await db.commit()
        await db.refresh(assistant_message)

        # Format response
        return MessageResponse(
            id=assistant_message.id,
            role=assistant_message.role,
            content=assistant_message.content,
            agent_used=assistant_message.agent_used,
            sources=[s for s in response.get("sources", [])],
            response_time_ms=response_time_ms,
            created_at=assistant_message.created_at
        )

    except Exception as e:
        logger.error(f"Error processing message: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )


@router.post("/chat/stream")
async def create_message_stream(
    message_data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a message with streaming response"""

    async def generate_stream() -> AsyncGenerator[str, None]:
        """Generate SSE stream"""
        try:
            # Send initial acknowledgment
            yield f"data: {json.dumps({'type': 'start', 'message': 'Processing your request...'})}\n\n"

            # Get or create chat (similar to non-streaming)
            if message_data.chat_id:
                result = await db.execute(
                    select(Chat).where(
                        Chat.id == message_data.chat_id,
                        Chat.user_id == current_user.id
                    )
                )
                chat = result.scalar_one_or_none()
                if not chat:
                    yield f"data: {json.dumps({'type': 'error', 'message': 'Chat not found'})}\n\n"
                    return
            else:
                chat = Chat(
                    user_id=current_user.id,
                    title=message_data.content[:50] + "..."
                )
                db.add(chat)
                await db.commit()
                await db.refresh(chat)

            # Save user message
            user_message = Message(
                chat_id=chat.id,
                user_id=current_user.id,
                role="user",
                content=message_data.content
            )
            db.add(user_message)
            await db.commit()

            # Get chat history
            result = await db.execute(
                select(Message).where(Message.chat_id == chat.id).order_by(Message.created_at)
            )
            messages = result.scalars().all()

            # Convert to LangChain messages (excluding the current user message)
            chat_history = []
            for msg in messages[:-1]:  # Exclude the current message
                if msg.role == "user":
                    chat_history.append(HumanMessage(content=msg.content))
                elif msg.role == "assistant":
                    chat_history.append(AIMessage(content=msg.content))

            # Stream tokens from orchestrator
            full_response = ""
            agents_used = []
            sources = []

            async for chunk in get_orchestrator().stream_process(
                query=message_data.content,
                chat_history=chat_history
            ):
                if chunk.get("type") == "token":
                    token = chunk.get("content", "")
                    full_response += token
                    yield f"data: {json.dumps({'type': 'token', 'content': token})}\n\n"
                elif chunk.get("type") == "agents_used":
                    agents_used = chunk.get("agents", [])
                elif chunk.get("type") == "sources":
                    sources = chunk.get("sources", [])
                    # Stream citations to frontend
                    yield f"data: {json.dumps({'type': 'citation', 'citations': sources})}\n\n"

            # Save the complete response to database
            assistant_message = Message(
                chat_id=chat.id,
                user_id=current_user.id,
                role="assistant",
                content=full_response,
                agent_used=", ".join(agents_used),
                sources_json=json.dumps(sources) if sources else None
            )
            db.add(assistant_message)
            await db.commit()

            # Send completion
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )


@router.get("/chats", response_model=ChatListResponse)
async def list_chats(
    page: int = 1,
    per_page: int = 20,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """List user's chat sessions"""
    # Count total
    count_result = await db.execute(
        select(Chat).where(Chat.user_id == current_user.id)
    )
    total = len(count_result.scalars().all())

    # Get paginated results
    offset = (page - 1) * per_page
    result = await db.execute(
        select(Chat)
        .where(Chat.user_id == current_user.id)
        .order_by(Chat.updated_at.desc())
        .offset(offset)
        .limit(per_page)
    )
    chats = result.scalars().all()

    # Convert to response
    chat_responses = []
    for chat in chats:
        # Get messages for this chat
        msg_result = await db.execute(
            select(Message)
            .where(Message.chat_id == chat.id)
            .order_by(Message.created_at)
        )
        messages = msg_result.scalars().all()

        chat_resp = ChatResponse(
            id=chat.id,
            title=chat.title,
            created_at=chat.created_at,
            updated_at=chat.updated_at,
            total_tokens_used=chat.total_tokens_used,
            total_cost=chat.total_cost,
            messages=[
                MessageResponse(
                    id=msg.id,
                    role=msg.role,
                    content=msg.content,
                    created_at=msg.created_at
                )
                for msg in messages
            ]
        )
        chat_responses.append(chat_resp)

    return ChatListResponse(
        chats=chat_responses,
        total=total,
        page=page,
        per_page=per_page
    )


@router.get("/chats/{chat_id}", response_model=ChatResponse)
async def get_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get a specific chat with messages"""
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    # Get messages
    msg_result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat.id)
        .order_by(Message.created_at)
    )
    messages = msg_result.scalars().all()

    return ChatResponse(
        id=chat.id,
        title=chat.title,
        created_at=chat.created_at,
        updated_at=chat.updated_at,
        total_tokens_used=chat.total_tokens_used,
        total_cost=chat.total_cost,
        messages=[
            MessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                agent_used=msg.agent_used,
                sources=json.loads(msg.sources_json) if msg.sources_json else [],
                created_at=msg.created_at
            )
            for msg in messages
        ]
    )


@router.delete("/chats/{chat_id}")
async def delete_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Delete a chat session"""
    result = await db.execute(
        select(Chat).where(
            Chat.id == chat_id,
            Chat.user_id == current_user.id
        )
    )
    chat = result.scalar_one_or_none()

    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found"
        )

    await db.delete(chat)
    await db.commit()

    return {"message": "Chat deleted successfully"}


# Add missing import
import asyncio