from fastapi import APIRouter
from app.core.config import settings
from app.services import document_manager

router = APIRouter(prefix="/api/health", tags=["health"])


@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "version": settings.APP_VERSION,
        "model": settings.OPENAI_MODEL,
        "documents_count": len(document_manager.uploaded_files),
    }


@router.get("/model")
async def model_health_check():
    from app.services.llm_service import llm_service

    try:
        test_response = llm_service.llm.invoke("你好")
        return {
            "model_status": "connected",
            "model": settings.OPENAI_MODEL,
            "test_response": "success",
        }
    except Exception as e:
        return {
            "model_status": "error",
            "model": settings.OPENAI_MODEL,
            "error": str(e),
        }
