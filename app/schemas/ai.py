from typing import Any

from pydantic import BaseModel


class SummarizeRequest(BaseModel):
    text: str


class ParagraphSummary(BaseModel):
    index: int
    text: str
    summary: dict[str, Any]


class DocumentSummary(BaseModel):
    paragraphs: list[ParagraphSummary]
    combined_summary: dict[str, Any] | None


class ParagraphsOnlyResponse(BaseModel):
    paragraphs: list[ParagraphSummary]


class SummarizeResponse(BaseModel):
    document_summary: DocumentSummary


class AskRequest(BaseModel):
    question: str
    context: str | None = None


class AskResponse(BaseModel):
    answer: str


class QuestionsRequest(BaseModel):
    text: str
    count: int = 5


class QuestionsResponse(BaseModel):
    questions: list[str]