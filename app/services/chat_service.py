import json
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path
from app.core.config import settings
from app.core.logger import get_logger
from app.models.schemas import ChatSession

logger = get_logger("chat_service")

SESSION_FILE = "data/chat_sessions.json"


class ChatService:
    def __init__(self):
        self.sessions_meta: Dict[str, Dict[str, Any]] = {}
        self._load_sessions()

    def _load_sessions(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    self.sessions_meta = json.load(f)
                logger.info(f"Loaded {len(self.sessions_meta)} sessions from storage")
            except Exception as e:
                logger.error(f"Failed to load sessions: {e}")
                self.sessions_meta = {}
        else:
            Path(SESSION_FILE).parent.mkdir(parents=True, exist_ok=True)

    def _save_sessions(self):
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(self.sessions_meta, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")

    def create_session(self, session_id: str):
        if session_id not in self.sessions_meta:
            self.sessions_meta[session_id] = {
                "session_id": session_id,
                "created_at": datetime.now().isoformat(),
                "last_message": None,
                "message_count": 0,
                "history": [],
            }
            self._save_sessions()
            logger.info(f"Created session: {session_id}")

    def update_session(self, session_id: str, last_message: str):
        if session_id in self.sessions_meta:
            self.sessions_meta[session_id]["last_message"] = last_message
            self.sessions_meta[session_id]["message_count"] = (
                self.sessions_meta[session_id].get("message_count", 0) + 1
            )
            self._save_sessions()

    def add_message(self, session_id: str, msg_type: str, content: Any):
        if session_id not in self.sessions_meta:
            self.create_session(session_id)

        if "history" not in self.sessions_meta[session_id]:
            self.sessions_meta[session_id]["history"] = []

        self.sessions_meta[session_id]["history"].append(
            {
                "type": msg_type,
                "content": str(content),
                "timestamp": datetime.now().isoformat(),
            }
        )
        self._save_sessions()

    def get_history(self, session_id: str) -> List[Dict[str, Any]]:
        if session_id in self.sessions_meta:
            return self.sessions_meta[session_id].get("history", [])
        return []

    def get_sessions(self) -> List[ChatSession]:
        sessions = list(self.sessions_meta.values())
        sessions.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return [
            ChatSession(
                session_id=s["session_id"],
                created_at=datetime.fromisoformat(s["created_at"]),
                last_message=s.get("last_message"),
                message_count=s.get("message_count", 0),
            )
            for s in sessions
        ]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self.sessions_meta.get(session_id)

    def delete_session(self, session_id: str) -> bool:
        if session_id in self.sessions_meta:
            del self.sessions_meta[session_id]
            self._save_sessions()
            logger.info(f"Deleted session: {session_id}")
            return True
        return False


chat_service = ChatService()
