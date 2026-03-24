import uuid
from typing import Literal
from pydantic import BaseModel, ConfigDict
from app.models.enums import DifficultyLevel, SummaryType

class SummarizeRequest(BaseModel):
    text: str
    summary_type: SummaryType = SummaryType.DETAILED

class SummaryChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    chunk_order: int
    relevance_score: float

class SummaryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    summary_id: uuid.UUID
    summary_title: str
    summary_content: str
    summary_type: SummaryType

class AskRequest(BaseModel):
    project_id: uuid.UUID
    question: str
    selected_material_ids: list[uuid.UUID] | None = None
    stream: bool = True

class CitationItem(BaseModel):
    source_label: str
    chunk_id: uuid.UUID
    material_id: uuid.UUID | None = None
    filename: str | None = None
    chunk_index: int | None = None
    page_number: int | None = None
    slide_number: int | None = None
    section_heading: str | None = None
    retrieval_score: float | None = None
    rank: int
    excerpt: str | None = None

class GroundingEventData(BaseModel):
    sources: list[CitationItem]

class DoneEventData(BaseModel):
    citations: list[CitationItem]

class SSEGroundingEvent(BaseModel):
    event: Literal["grounding"] = "grounding"
    data: GroundingEventData

class SSETokenEvent(BaseModel):
    event: Literal["token"] = "token"
    data: str

class SSEDoneEvent(BaseModel):
    event: Literal["done"] = "done"
    data: DoneEventData

class AskResponse(BaseModel):
    answer: str
    citations: list[CitationItem] = []
    grounding_context: list[CitationItem] = []

class QuestionsRequest(BaseModel):
    text: str
    count: int = 5
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM

class QuestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    question_id: uuid.UUID
    question_text: str
    difficulty_level: DifficultyLevel

class QuestionsResponse(BaseModel):
    questions: list[QuestionRead]