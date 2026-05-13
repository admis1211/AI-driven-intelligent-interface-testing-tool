from fastapi import APIRouter, UploadFile, File, HTTPException
from app.models.schemas import DocumentListResponse, DocumentUpload
from app.core.config import settings
from app.services import document_manager
import os
import aiofiles

router = APIRouter(prefix="/api/documents", tags=["documents"])


@router.post("/upload")
async def upload_document(file: UploadFile = File(...)):
    if file.size and file.size > settings.MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=400, detail="文件大小超出限制")

    file_ext = os.path.splitext(file.filename or "")[1].lower()
    allowed_extensions = [
        ".txt",
        ".pdf",
        ".docx",
        ".pptx",
        ".ppt",
        ".md",
        ".png",
        ".jpg",
        ".jpeg",
        ".bmp",
        ".gif",
        ".tiff",
        ".webp",
    ]

    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型。支持: {', '.join(allowed_extensions)}",
        )

    file_path = os.path.join(settings.UPLOAD_DIR, file.filename or "unknown")

    try:
        async with aiofiles.open(file_path, "wb") as f:
            content = await file.read()
            await f.write(content)

        doc = document_manager.add_document(file.filename or "unknown", len(content))

        return {
            "message": "文件上传成功",
            "document": doc,
            "document_count": len(document_manager.uploaded_files),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")


@router.get("/", response_model=DocumentListResponse)
async def list_documents():
    docs = document_manager.get_all_documents()
    return DocumentListResponse(documents=docs, total=len(docs))


@router.delete("/{filename}")
async def delete_document(filename: str):
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    if os.path.exists(file_path):
        os.remove(file_path)

    if document_manager.remove_document(filename):
        return {"message": f"文件 {filename} 已删除"}

    raise HTTPException(status_code=404, detail="文件不存在")


@router.delete("/")
async def clear_all_documents():
    for doc in document_manager.uploaded_files:
        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
        if os.path.exists(file_path):
            os.remove(file_path)

    document_manager.clear_all_documents()
    return {"message": "所有文档已清除"}


@router.get("/stats")
async def get_stats():
    total_size = 0
    for doc in document_manager.uploaded_files:
        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
        if os.path.exists(file_path):
            total_size += os.path.getsize(file_path)

    return {
        "total_documents": len(document_manager.uploaded_files),
        "total_size": total_size,
    }
