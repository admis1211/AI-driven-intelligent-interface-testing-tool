import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict


class StructuredLogger:
    def __init__(self, name: str, log_file: str = "logs/app.log"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra=kwargs)

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra=kwargs)

    def upload_event(self, filename: str, status: str, **kwargs):
        event = {
            "event_type": "upload",
            "filename": filename,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            **kwargs,
        }
        self.logger.info(f"UPLOAD: {json.dumps(event)}")

    def document_read_event(self, filename: str, content_length: int, status: str):
        event = {
            "event_type": "document_read",
            "filename": filename,
            "content_length": content_length,
            "status": status,
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(f"DOC_READ: {json.dumps(event)}")

    def chat_event(self, session_id: str, use_context: bool, has_sources: bool):
        event = {
            "event_type": "chat",
            "session_id": session_id,
            "use_context": use_context,
            "has_sources": has_sources,
            "timestamp": datetime.now().isoformat(),
        }
        self.logger.info(f"CHAT: {json.dumps(event)}")


def get_logger(name: str) -> StructuredLogger:
    return StructuredLogger(name)
