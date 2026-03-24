from datetime import datetime
import uuid
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.enums import ProjectRole


class ProjectMember(Base):
    __tablename__ = "project_members"
    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_members_user_project"),
    )

    project_member_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    project_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("projects.project_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="CASCADE", onupdate="CASCADE"), index=True, nullable=False)
    invited_by: Mapped[Optional[uuid.UUID]] = mapped_column(UUID(as_uuid=True), ForeignKey("users.user_id", ondelete="SET NULL", onupdate="CASCADE"), nullable=True)
    role: Mapped[ProjectRole] = mapped_column(Enum(ProjectRole, name="project_role"), default=ProjectRole.VIEWER, nullable=False, index=True)
    joined_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)