from pydantic import BaseModel


class DocumentCreate(BaseModel):
    filename: str
    s3_key: str


class DocumentRead(BaseModel):
    id: int
    project_id: int
    filename: str
    s3_key: str
    status: str