import uuid
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.enums import ProjectRole

class ProjectMemberCreate(BaseModel):
    email: EmailStr
    role: ProjectRole = ProjectRole.VIEWER

class ProjectMemberRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    project_member_id: uuid.UUID
    user_id: uuid.UUID
    role: ProjectRole
    # Available if joined with Users table
    email: EmailStr | None = None