from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str


class ProjectRead(BaseModel):
    id: int
    name: str


class ProjectList(BaseModel):
    items: list[ProjectRead]