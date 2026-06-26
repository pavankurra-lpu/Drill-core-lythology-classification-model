"""
Chatbot router — sessions, messages, RAG document indexing, and semantic search.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.dependencies import get_current_active_user, get_db
from app.models.chat import ChatMessage, ChatSession
from app.models.user import User
from app.schemas.chat import (
    ChatMessageCreate,
    ChatMessageResponse,
    ChatMessagesListResponse,
    ChatSessionCreate,
    ChatSessionListResponse,
    ChatSessionResponse,
    RAGSearchRequest,
    RAGSearchResponse,
    RAGSearchResult,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chatbot"])

RAG_DOCS_DIR = Path(settings.UPLOAD_DIR) / "rag_docs"
RAG_DOCS_DIR.mkdir(parents=True, exist_ok=True)


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session",
)
async def create_session(
    data: ChatSessionCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionResponse:
    session = ChatSession(
        user_id=current_user.id,
        title=data.title,
        description=data.description,
        prediction_id=data.prediction_id,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)
    logger.info("Chat session created: id=%s user_id=%s", session.id, current_user.id)
    return ChatSessionResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List all chat sessions for the current user",
)
async def list_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatSessionListResponse:
    total_result = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == current_user.id)
    )
    total = total_result.scalar_one()

    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.updated_at.desc())
    )
    sessions = result.scalars().all()
    return ChatSessionListResponse(
        items=[ChatSessionResponse.model_validate(s) for s in sessions],
        total=total,
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session and all its messages",
)
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await db.delete(session)
    logger.info("Chat session deleted: id=%s", session_id)


# ── Messages ──────────────────────────────────────────────────────────────────

@router.get(
    "/sessions/{session_id}/messages",
    response_model=ChatMessagesListResponse,
    summary="Retrieve all messages in a session",
)
async def get_messages(
    session_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessagesListResponse:
    # Verify session ownership
    sess_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    if not sess_result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    msg_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = msg_result.scalars().all()

    return ChatMessagesListResponse(
        session_id=session_id,
        messages=[ChatMessageResponse.model_validate(m) for m in messages],
        total=len(messages),
    )


@router.post(
    "/sessions/{session_id}/messages",
    response_model=ChatMessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message and get an AI response",
)
async def send_message(
    session_id: int,
    body: ChatMessageCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ChatMessageResponse:
    """
    Persist the user message, invoke the LLM (optionally with RAG context),
    persist the assistant reply, and return it.
    """
    # Verify session
    sess_result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    session = sess_result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")

    # Persist user message
    user_msg = ChatMessage(
        session_id=session_id,
        role="user",
        content=body.content,
    )
    db.add(user_msg)
    await db.flush()

    # Build context from RAG
    context = ""
    if body.use_rag:
        try:
            from app.services.rag_service import rag_service  # noqa: PLC0415

            context = await rag_service.get_context_async(body.content)
        except Exception as exc:
            logger.warning("RAG context fetch failed: %s", exc)

    # Build prompt with history
    history_result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .limit(20)
    )
    history = history_result.scalars().all()

    history_text = "\n".join(
        f"{m.role.upper()}: {m.content}" for m in history[:-1]
    )

    prompt = (
        f"{history_text}\n\nUSER: {body.content}"
        if history_text
        else body.content
    )

    # Call LLM
    try:
        from app.services.llm_service import llm_service  # noqa: PLC0415

        response_text = llm_service.generate_response(prompt=prompt, context=context)
    except Exception as exc:
        logger.error("LLM generation failed: %s", exc)
        response_text = (
            "I'm sorry, I couldn't generate a response at this time. "
            "Please try again later."
        )

    # Persist assistant response
    assistant_msg = ChatMessage(
        session_id=session_id,
        role="assistant",
        content=response_text,
        metadata_={"used_rag": body.use_rag, "context_length": len(context)},
    )
    db.add(assistant_msg)
    await db.flush()
    await db.refresh(assistant_msg)

    logger.info(
        "Chat message processed: session_id=%s user_id=%s",
        session_id, current_user.id,
    )
    return ChatMessageResponse.model_validate(assistant_msg)


# ── RAG ───────────────────────────────────────────────────────────────────────

@router.post(
    "/rag/upload",
    summary="Upload a PDF document to the RAG knowledge base",
)
async def upload_rag_document(
    file: UploadFile = File(..., description="PDF document to index"),
    current_user: User = Depends(get_current_active_user),
) -> dict:
    """Index a PDF document into the FAISS vector store for RAG retrieval."""
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only PDF files are supported",
        )

    content = await file.read()
    save_path = RAG_DOCS_DIR / (file.filename or "document.pdf")
    with open(save_path, "wb") as f:
        f.write(content)

    # Index asynchronously
    try:
        from app.services.rag_service import rag_service  # noqa: PLC0415

        num_chunks = rag_service.index_document(
            file_path=str(save_path),
            metadata={"source": file.filename, "uploaded_by": current_user.id},
        )
        logger.info(
            "RAG document indexed: file=%s chunks=%d user_id=%s",
            file.filename, num_chunks, current_user.id,
        )
        return {"message": "Document indexed successfully", "chunks": num_chunks}
    except Exception as exc:
        logger.error("RAG indexing failed: %s", exc)
        return {"message": f"Document saved but indexing failed: {exc}", "chunks": 0}


@router.post(
    "/search",
    response_model=RAGSearchResponse,
    summary="Semantic search over the RAG knowledge base",
)
async def rag_search(
    body: RAGSearchRequest,
    current_user: User = Depends(get_current_active_user),
) -> RAGSearchResponse:
    """Perform a similarity search over indexed documents."""
    try:
        from app.services.rag_service import rag_service  # noqa: PLC0415

        docs = rag_service.search(query=body.query, k=body.k)
        results = [
            RAGSearchResult(
                content=d.get("content", ""),
                score=d.get("score", 0.0),
                source=d.get("source"),
                metadata=d.get("metadata"),
            )
            for d in docs
        ]
    except Exception as exc:
        logger.error("RAG search failed: %s", exc)
        results = []

    return RAGSearchResponse(
        query=body.query,
        results=results,
        total=len(results),
    )
