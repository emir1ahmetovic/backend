from datetime import datetime
import uuid

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import MessageRole


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), index=True, nullable=False)
    role: Mapped[MessageRole] = mapped_column(Enum(MessageRole, name="message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_error: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class ChatMessageChunk(Base):
    __tablename__ = "chat_message_chunks"

    chat_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("chat_messages.chat_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material_chunks.material_chunk_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True, index=True)
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
    was_used_in_prompt: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
