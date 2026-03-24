from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector

from app.database import Base
from app.models.enums import FileType, ProcessingStatus, EmbeddingStatus


class Material(Base):
    __tablename__ = "materials"

    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    uploaded_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), index=True, nullable=False)
    original_file_name: Mapped[str] = mapped_column(String(512), nullable=False)
    file_type: Mapped[FileType] = mapped_column(Enum(FileType, name="file_type"), nullable=False)
    s3_bucket: Mapped[str] = mapped_column(String(255), nullable=False)
    s3_key: Mapped[str] = mapped_column(String(1024), nullable=False)
    processing_status: Mapped[ProcessingStatus] = mapped_column(Enum(ProcessingStatus, name="processing_status"), default=ProcessingStatus.PENDING, index=True, nullable=False)
    processing_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    total_chunks: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)


class MaterialChunk(Base):
    __tablename__ = "material_chunks"
    __table_args__ = (
        UniqueConstraint("material_id", "chunk_index", name="uq_material_chunks_material_index"),
    )

    material_chunk_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    material_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("materials.material_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    page_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    slide_number: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    section_heading: Mapped[Optional[str]] = mapped_column(String(512), nullable=True)
    chunk_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    embedding_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    embedding_model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    embedding_status: Mapped[EmbeddingStatus] = mapped_column(Enum(EmbeddingStatus, name="embedding_status"), default=EmbeddingStatus.PENDING, index=True, nullable=False)
    embedding = mapped_column(Vector(1536))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)