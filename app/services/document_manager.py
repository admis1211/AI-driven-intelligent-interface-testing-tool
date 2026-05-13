from datetime import datetime
from typing import List
from app.models.schemas import DocumentUpload
from app.services.storage import document_storage
from app.core.config import settings
from app.core.logger import get_logger
import os

logger = get_logger("document_manager")


def _sync_from_storage():
    """从持久化存储同步文档列表"""
    try:
        stored_docs = document_storage.get_all_documents()
        synced = []
        for doc in stored_docs:
            file_path = os.path.join(settings.UPLOAD_DIR, doc["filename"])
            if os.path.exists(file_path):
                synced.append(
                    DocumentUpload(
                        filename=doc["filename"],
                        size=doc["size"],
                        uploaded_at=datetime.fromisoformat(doc["uploaded_at"]),
                        status=doc.get("status", "active"),
                    )
                )
            else:
                logger.debug(f"File not found, skipping: {doc['filename']}")
        if synced:
            logger.info(f"Synced {len(synced)} documents from storage")
        return synced
    except Exception as e:
        logger.error(f"Sync from storage failed: {e}")
        return []


uploaded_files: List[DocumentUpload] = []


def init_document_manager():
    """初始化文档管理器，从存储同步"""
    global uploaded_files
    document_storage.sync_with_filesystem(settings.UPLOAD_DIR)
    uploaded_files = _sync_from_storage()


init_document_manager()


def add_document(filename: str, size: int) -> DocumentUpload:
    file_path = os.path.join(settings.UPLOAD_DIR, filename)

    result = document_storage.add_document(filename, file_path, size)

    if result["status"] == "duplicate":
        logger.upload_event(filename, "duplicate", size=size)
        return DocumentUpload(
            filename=filename, size=size, uploaded_at=datetime.now(), status="duplicate"
        )

    doc = DocumentUpload(
        filename=filename,
        size=size,
        uploaded_at=datetime.now(),
        status="uploaded",
    )
    uploaded_files.append(doc)

    logger.upload_event(filename, "added", size=size)
    return doc


def remove_document(filename: str) -> bool:
    global uploaded_files

    storage_removed = document_storage.remove_document(filename)

    for i, doc in enumerate(uploaded_files):
        if doc.filename == filename:
            uploaded_files.pop(i)
            logger.upload_event(filename, "removed")
            return True

    return storage_removed


def clear_all_documents():
    global uploaded_files

    for doc in uploaded_files:
        file_path = os.path.join(settings.UPLOAD_DIR, doc.filename)
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.debug(f"Deleted file: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete file {file_path}: {e}")

    uploaded_files = []
    document_storage.clear_all()
    logger.info("All documents cleared")


def get_all_documents() -> List[DocumentUpload]:
    return uploaded_files


def sync_with_filesystem():
    """同步文件系统与存储"""
    result = document_storage.sync_with_filesystem(settings.UPLOAD_DIR)
    global uploaded_files
    uploaded_files = _sync_from_storage()
    return result
