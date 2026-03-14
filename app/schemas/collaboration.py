from pydantic import BaseModel, EmailStr


class ProjectMemberCreate(BaseModel):
    email: EmailStr
    role: str = "member"


class ProjectMemberRead(BaseModel):
    id: int
    email: EmailStr
    role: str