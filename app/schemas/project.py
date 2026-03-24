import uuid
from pydantic import BaseModel, ConfigDict

class ProjectCreate(BaseModel):
    project_name: str
    project_description: str | None = None

class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    project_id: uuid.UUID
    project_name: str
    project_description: str | None
    owner_id: uuid.UUID
    status: str

class ProjectList(BaseModel):
    items: list[ProjectRead]