import json
import hashlib
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from app.core.config import settings
from app.core.logger import get_logger

logger = get_logger("storage")


class DocumentStorage:
    def __init__(self, storage_file: str = "data/documents.json"):
        self.storage_file = storage_file
        Path(self.storage_file).parent.mkdir(parents=True, exist_ok=True)
        self._ensure_storage_exists()

    def _ensure_storage_exists(self):
        if not Path(self.storage_file).exists():
            self._save(
                {
                    "version": "1.0",
                    "documents": [],
                    "last_updated": datetime.now().isoformat(),
                }
            )

    def _load(self) -> Dict:
        try:
            with open(self.storage_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load storage: {e}")
            return {
                "version": "1.0",
                "documents": [],
                "last_updated": datetime.now().isoformat(),
            }

    def _save(self, data: Dict):
        try:
            data["last_updated"] = datetime.now().isoformat()
            with open(self.storage_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save storage: {e}")

    def _compute_file_hash(self, file_path: str) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_document(self, filename: str, file_path: str, size: int) -> Dict:
        data = self._load()

        file_hash = self._compute_file_hash(file_path)

        for doc in data["documents"]:
            if doc.get("file_hash") == file_hash:
                logger.info(f"Duplicate document detected: {filename}")
                return {"status": "duplicate", "document": doc}

        doc = {
            "id": f"doc_{len(data['documents']) + 1}_{int(datetime.now().timestamp())}",
            "filename": filename,
            "size": size,
            "file_hash": file_hash,
            "uploaded_at": datetime.now().isoformat(),
            "status": "active",
        }

        data["documents"].append(doc)
        self._save(data)

        logger.info(f"Document added to storage: {filename}")
        return {"status": "added", "document": doc}

    def remove_document(self, filename: str) -> bool:
        data = self._load()
        original_len = len(data["documents"])
        data["documents"] = [d for d in data["documents"] if d["filename"] != filename]

        if len(data["documents"]) < original_len:
            self._save(data)
            logger.info(f"Document removed from storage: {filename}")
            return True
        return False

    def get_all_documents(self) -> List[Dict]:
        data = self._load()
        return data.get("documents", [])

    def clear_all(self):
        self._save(
            {
                "version": "1.0",
                "documents": [],
                "last_updated": datetime.now().isoformat(),
            }
        )
        logger.info("All documents cleared from storage")

    def sync_with_filesystem(self, upload_dir: str) -> Dict:
        data = self._load()
        existing_files = set()

        if not os.path.exists(upload_dir):
            os.makedirs(upload_dir, exist_ok=True)
            return {"synced": 0, "status": "directory_created"}

        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                existing_files.add(filename)

                file_hash = self._compute_file_hash(file_path)
                exists = any(d.get("file_hash") == file_hash for d in data["documents"])

                if not exists:
                    doc = {
                        "id": f"doc_{len(data['documents']) + 1}_{int(datetime.now().timestamp())}",
                        "filename": filename,
                        "size": os.path.getsize(file_path),
                        "file_hash": file_hash,
                        "uploaded_at": datetime.now().isoformat(),
                        "status": "synced",
                    }
                    data["documents"].append(doc)
                    logger.info(f"Synced document from filesystem: {filename}")

        data["documents"] = [
            d for d in data["documents"] if d["filename"] in existing_files
        ]
        self._save(data)

        logger.info(f"Storage sync completed: {len(data['documents'])} documents")
        return {"synced": len(data["documents"]), "status": "completed"}


document_storage = DocumentStorage()
