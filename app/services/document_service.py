from langchain_community.document_loaders import TextLoader, PyPDFLoader, Docx2txtLoader
from langchain.document_loaders import UnstructuredPowerPointLoader as PPTXLoader
from pathlib import Path
from typing import List, Optional
import os
from app.services.ocr_service import ocr_service
from app.core.logger import get_logger

logger = get_logger("document_service")


class DocumentReader:
    def __init__(self):
        self.loaders = {
            ".txt": lambda fp: TextLoader(fp, encoding="utf-8"),
            ".md": lambda fp: TextLoader(fp, encoding="utf-8"),
            ".pdf": PyPDFLoader,
            ".docx": Docx2txtLoader,
            ".pptx": PPTXLoader,
            ".ppt": PPTXLoader,
        }
        self.image_extensions = {
            ".png",
            ".jpg",
            ".jpeg",
            ".bmp",
            ".gif",
            ".tiff",
            ".webp",
        }

    def read_document(self, file_path: str) -> str:
        ext = Path(file_path).suffix.lower()

        if ext in self.image_extensions:
            content = ocr_service.extract_text_from_image(file_path)
            logger.document_read_event(file_path, len(content), "success")
            return content

        loader_class = self.loaders.get(ext)
        if not loader_class:
            raise ValueError(f"Unsupported file type: {ext}")

        try:
            loader = loader_class(file_path)
            documents = loader.load()

            if not documents:
                logger.document_read_event(file_path, 0, "empty")
                return ""

            content_parts = []
            for doc in documents:
                content = doc.page_content.strip()
                if content:
                    content_parts.append(content)

            result = "\n\n".join(content_parts)
            logger.document_read_event(file_path, len(result), "success")
            return result
        except Exception as e:
            logger.document_read_event(file_path, 0, f"error: {str(e)}")
            raise

    def read_all_documents(self, file_paths: List[str]) -> str:
        all_contents = []

        for file_path in file_paths:
            try:
                content = self.read_document(file_path)
                if content:
                    filename = os.path.basename(file_path)
                    all_contents.append(f"文档: {filename}\n{content}")
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
                continue

        if not all_contents:
            return ""

        context = "\n\n---\n\n".join(all_contents)
        logger.info(
            f"Context prepared: {len(context)} chars from {len(file_paths)} files"
        )
        return context


document_reader = DocumentReader()
