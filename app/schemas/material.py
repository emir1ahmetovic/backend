import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.enums import FileType, ProcessingStatus

class MaterialCreate(BaseModel):
    original_file_name: str
    file_type: FileType
    s3_bucket: str
    s3_key: str

class MaterialRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    material_id: uuid.UUID
    project_id: uuid.UUID
    uploaded_by: uuid.UUID
    original_file_name: str
    file_type: FileType
    processing_status: ProcessingStatus
    page_count: int | None
    total_chunks: int | None
    created_at: datetime
