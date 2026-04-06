"""
Context History Management for AI Agents — moved from db/context_history.py.
"""
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy import Column, DateTime, String, JSON, ForeignKey
from sqlalchemy.orm import Session, relationship

from database.schema import Base, engine


class ContextMessage(Base):
    """Individual message in the conversation history."""
    __tablename__ = "context_messages"

    id = Column(String, primary_key=True, default=lambda: f"msg_{datetime.utcnow().timestamp()}")
    thread_id = Column(String, index=True, nullable=False)
    user_id = Column(String, ForeignKey("users.id"), index=True, nullable=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    message_metadata = Column("metadata", JSON, nullable=True)


Base.metadata.create_all(engine, tables=[ContextMessage.__table__])


class ContextHistoryManager:
    """Manages conversation context history with a rolling buffer approach."""

    def __init__(self, thread_id: str, user_id: Optional[str] = None, max_history_length: int = 20):
        self.thread_id = thread_id
        self.user_id = user_id
        self.max_history_length = max_history_length
        Base.metadata.create_all(engine, tables=[ContextMessage.__table__])

    def add_message(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> ContextMessage:
        if role not in ("user", "assistant"):
            raise ValueError("Role must be 'user' or 'assistant'")
        with Session(engine) as session:
            message = ContextMessage(
                thread_id=self.thread_id,
                user_id=self.user_id,
                role=role,
                content=content,
                message_metadata=metadata,
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            self._enforce_limit(session)
            return message

    def _enforce_limit(self, session: Session) -> None:
        total = session.query(ContextMessage).filter(ContextMessage.thread_id == self.thread_id).count()
        if total > self.max_history_length:
            excess = total - self.max_history_length
            old = (
                session.query(ContextMessage)
                .filter(ContextMessage.thread_id == self.thread_id)
                .order_by(ContextMessage.created_at.asc())
                .limit(excess)
                .all()
            )
            for msg in old:
                session.delete(msg)
            session.commit()

    def get_history(self, max_messages: Optional[int] = None, include_metadata: bool = False) -> List[Dict[str, Any]]:
        with Session(engine) as session:
            query = (
                session.query(ContextMessage)
                .filter(ContextMessage.thread_id == self.thread_id)
                .order_by(ContextMessage.created_at.asc())
            )
            if max_messages:
                query = query.limit(max_messages)
            messages = []
            for msg in query.all():
                entry = {"role": msg.role, "content": msg.content, "created_at": msg.created_at.isoformat()}
                if include_metadata and msg.message_metadata:
                    entry["metadata"] = msg.message_metadata
                messages.append(entry)
            return messages

    def get_history_as_string(self, max_messages: Optional[int] = None) -> str:
        history = self.get_history(max_messages=max_messages)
        if not history:
            return "[No conversation history yet]"
        lines = ["--- Conversation History ---"]
        for msg in history:
            lines.append(f"{msg['role'].upper()}: {msg['content']}")
        lines.append("--- End History ---")
        return "\n".join(lines)

    def clear_history(self) -> None:
        with Session(engine) as session:
            session.query(ContextMessage).filter(ContextMessage.thread_id == self.thread_id).delete()
            session.commit()

    def get_message_count(self) -> int:
        with Session(engine) as session:
            return session.query(ContextMessage).filter(ContextMessage.thread_id == self.thread_id).count()

    def get_context_for_agent(self, max_messages: int = 10) -> str:
        history = self.get_history(max_messages=max_messages)
        if not history:
            return "Context: This is a new conversation with no prior history."
        lines = ["Previous conversation context:"]
        for msg in history:
            lines.append(f"  {msg['role']}: {msg['content']}")
        return "\n".join(lines)


def get_manager(thread_id: str, user_id: Optional[str] = None, max_history_length: int = 20) -> ContextHistoryManager:
    return ContextHistoryManager(thread_id, user_id, max_history_length)


def add_to_history(
    thread_id: str,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
    user_id: Optional[str] = None,
) -> None:
    ContextHistoryManager(thread_id, user_id).add_message(role, content, metadata)


def get_conversation_history(thread_id: str, max_messages: Optional[int] = None) -> List[Dict[str, Any]]:
    return ContextHistoryManager(thread_id).get_history(max_messages=max_messages)
