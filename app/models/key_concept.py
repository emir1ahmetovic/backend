from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class KeyConcept(Base):
    __tablename__ = "key_concepts"

    key_concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), nullable=False)
    concept_name: Mapped[str] = mapped_column(String(255), nullable=False)
    concept_definition: Mapped[str] = mapped_column(Text, nullable=False)
    concept_category: Mapped[Optional[str]] = mapped_column(String(100), index=True, nullable=True)
    ai_model: Mapped[str] = mapped_column(String(100), nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


class KeyConceptChunk(Base):
    __tablename__ = "key_concept_chunks"

    key_concept_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("key_concepts.key_concept_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True)
    chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("material_chunks.material_chunk_id", ondelete="CASCADE", onupdate="CASCADE"), primary_key=True, index=True)
    relevance_score: Mapped[int] = mapped_column(Integer, nullable=False)
