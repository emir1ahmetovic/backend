from datetime import datetime
import uuid

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Float, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import SummaryType


class Summary(Base):
    __tablename__ = "summaries"

    summary_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), index=True, nullable=False)
    summary_title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_content: Mapped[str] = mapped_column(Text, nullable=False)
    summary_type: Mapped[SummaryType] = mapped_column(Enum(SummaryType, name="summary_type"), default=SummaryType.DETAILED, index=True, nullable=False)
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


class SummaryChunk(Base):
    __tablename__ = "summary_chunks"

    summary_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("summaries.summary_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material_chunks.material_chunk_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True, index=True)
    relevance_score: Mapped[float] = mapped_column(Float, nullable=False)
    chunk_order: Mapped[int] = mapped_column(Integer, nullable=False)
