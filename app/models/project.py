from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ProjectStatus


class Project(Base):
    __tablename__ = "projects"

    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    owner_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="RESTRICT", onupdate="CASCADE"), index=True, nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=False)
    project_description: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    project_status: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[ProjectStatus] = mapped_column(Enum(ProjectStatus, name="project_status"), default=ProjectStatus.ACTIVE, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), index=True, nullable=True)