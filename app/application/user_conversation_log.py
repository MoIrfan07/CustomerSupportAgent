from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.application.context_summarizer import ContextSummarizer

logger = logging.getLogger(__name__)


class UserConversationLog:
    """Persist and compact each authenticated user's conversation history."""

    def __init__(self, directory: Path | None = None) -> None:
        self.directory = directory or (
            Path(__file__).resolve().parents[2] / "data" / "user_logs"
        )
        self.summarizer = ContextSummarizer()

    def ensure_exists(self, user_identifier: str) -> Path:
        path = self._path_for(user_identifier)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        return path

    def list_chat_ids(self, user_identifier: str) -> list[str]:
        chat_directory = self._chat_directory(user_identifier)
        if not chat_directory.exists():
            return []
        chat_ids = [
            path.stem
            for path in chat_directory.glob("chat*.txt")
            if re.fullmatch(r"chat[1-9][0-9]*", path.stem)
        ]
        return sorted(chat_ids, key=lambda chat_id: int(chat_id[4:]))

    def next_chat_id(self, user_identifier: str) -> str:
        chat_ids = self.list_chat_ids(user_identifier)
        next_number = max((int(chat_id[4:]) for chat_id in chat_ids), default=0) + 1
        return f"chat{next_number}"

    def append_turn(
        self,
        user_identifier: str,
        *,
        user_message: str,
        assistant_message: str,
        chat_id: str = "chat1",
    ) -> None:
        path = self._chat_path(user_identifier, chat_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.touch(exist_ok=True)
        entries = (
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": "user",
                "content": user_message,
            },
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "role": "assistant",
                "content": assistant_message,
            },
        )
        with path.open("a", encoding="utf-8") as file:
            for entry in entries:
                file.write(json.dumps(entry, ensure_ascii=True) + "\n")

    def load_compressed_context(
        self,
        user_identifier: str,
        chat_id: str = "chat1",
    ) -> SystemMessage | None:
        path = self._chat_path(user_identifier, chat_id)
        messages: list[BaseMessage] = []
        legacy_path = self._path_for(user_identifier)
        if chat_id == "chat1" and legacy_path.exists():
            messages.extend(self._read_messages(legacy_path))
        if path.exists():
            messages.extend(self._read_messages(path))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
        if not messages:
            return None

        summary = self.summarizer.summarize(
            {"messages": messages},
            messages_to_summarize=messages,
        )
        content = json.dumps(summary, ensure_ascii=True, separators=(",", ":"))
        logger.info(
            "USER CONVERSATION CONTEXT | user=%s | messages=%s | compressed=true",
            user_identifier,
            len(messages),
        )
        return SystemMessage(
            content="Previous conversation context (compressed):\n" + content
        )

    def _path_for(self, user_identifier: str) -> Path:
        safe_identifier = re.sub(r"[^a-zA-Z0-9_.-]", "_", user_identifier).lower()
        if not safe_identifier:
            raise ValueError("A non-empty user identifier is required")
        return self.directory / f"{safe_identifier}.txt"

    def _chat_directory(self, user_identifier: str) -> Path:
        safe_identifier = self._safe_identifier(user_identifier)
        return self.directory / safe_identifier

    def _chat_path(self, user_identifier: str, chat_id: str) -> Path:
        if not re.fullmatch(r"chat[1-9][0-9]*", chat_id):
            raise ValueError("A valid chat identifier such as chat1 is required")
        return self._chat_directory(user_identifier) / f"{chat_id}.txt"

    @staticmethod
    def _safe_identifier(user_identifier: str) -> str:
        safe_identifier = re.sub(r"[^a-zA-Z0-9_.-]", "_", user_identifier).lower()
        if not safe_identifier:
            raise ValueError("A non-empty user identifier is required")
        return safe_identifier

    @staticmethod
    def _read_messages(path: Path) -> list[BaseMessage]:
        messages: list[BaseMessage] = []
        with path.open("r", encoding="utf-8") as file:
            for line_number, line in enumerate(file, start=1):
                if not line.strip():
                    continue
                try:
                    entry: dict[str, Any] = json.loads(line)
                except json.JSONDecodeError:
                    logger.warning(
                        "USER CONVERSATION LOG | invalid entry | file=%s | line=%s",
                        path,
                        line_number,
                    )
                    continue

                role = entry.get("role")
                content = entry.get("content")
                if not isinstance(content, str):
                    logger.warning(
                        "USER CONVERSATION LOG | invalid content | file=%s | line=%s",
                        path,
                        line_number,
                    )
                    continue
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        return messages
