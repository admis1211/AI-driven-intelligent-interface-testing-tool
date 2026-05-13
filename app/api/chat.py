from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from app.models.schemas import (
    ChatMessage,
    ChatResponse,
    ChatSessionListResponse,
    DeleteSessionResponse,
)
from app.services.llm_service import llm_service
from app.services.chat_service import chat_service
import json
import asyncio

router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("/", response_model=ChatResponse)
async def chat(message: ChatMessage):
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    result = await llm_service.chat(
        message=message.message,
        session_id=message.session_id,
        use_context=message.use_context,
        selected_documents=message.selected_documents,
    )

    return ChatResponse(
        response=result["response"],
        session_id=result["session_id"],
        sources=result.get("sources"),
    )


@router.post("/stream")
async def chat_stream(message: ChatMessage):
    if not message.message.strip():
        raise HTTPException(status_code=400, detail="消息不能为空")

    async def event_generator():
        async for chunk in llm_service.chat_stream(
            message=message.message,
            session_id=message.session_id,
            use_context=message.use_context,
            selected_documents=message.selected_documents,
        ):
            if chunk["type"] == "chunk":
                data = json.dumps({"type": "chunk", "content": chunk["content"]})
                yield f"data: {data}\n\n"
            elif chunk["type"] == "done":
                data = json.dumps(
                    {
                        "type": "done",
                        "session_id": chunk["session_id"],
                        "sources": chunk.get("sources"),
                    }
                )
                yield f"data: {data}\n\n"
            elif chunk["type"] == "error":
                data = json.dumps({"type": "error", "content": chunk["content"]})
                yield f"data: {data}\n\n"
            await asyncio.sleep(0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete("/session/{session_id}")
async def clear_session(session_id: str):
    success = llm_service.clear_session(session_id)
    if success:
        return {"message": "会话已清除"}
    raise HTTPException(status_code=404, detail="会话不存在")


@router.get("/sessions", response_model=ChatSessionListResponse)
async def get_sessions():
    """获取所有会话列表"""
    sessions = chat_service.get_sessions()
    return ChatSessionListResponse(sessions=sessions, total=len(sessions))


@router.get("/session/{session_id}/history")
async def get_session_history(session_id: str):
    """获取会话的聊天历史"""
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在或历史已过期")

    history = chat_service.get_history(session_id)

    return {"session_id": session_id, "history": history}


@router.get("/session/{session_id}")
async def get_session(session_id: str):
    """获取单个会话详情"""
    session = chat_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


@router.delete("/session/{session_id}/delete", response_model=DeleteSessionResponse)
async def delete_session(session_id: str):
    """删除会话"""
    chat_success = chat_service.delete_session(session_id)
    llm_success = llm_service.clear_session(session_id)

    if chat_success or llm_success:
        return DeleteSessionResponse(success=True, message="会话已删除")
    raise HTTPException(status_code=404, detail="会话不存在")
