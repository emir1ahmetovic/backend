from __future__ import annotations

from fastapi import APIRouter

from app.schemas.ai import (
    AskRequest,
    AskResponse,
    DocumentSummary,
    ParagraphSummary,
    ParagraphsOnlyResponse,
    QuestionsRequest,
    QuestionsResponse,
    SummarizeRequest,
    SummarizeResponse,
)
from app.services import bedrock
from app.services.summarization import summarize_by_paragraphs

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/summarize", response_model=SummarizeResponse)
def summarize(request: SummarizeRequest) -> SummarizeResponse:
    """
    Summarize a block of text using paragraph-based chunking and
    per-paragraph Bedrock summarization.
    """
    result = summarize_by_paragraphs(request.text)
    # Pydantic will coerce the dict structure into DocumentSummary / ParagraphSummary.
    return SummarizeResponse(document_summary=DocumentSummary(**result))


@router.post("/summarize/paragraphs", response_model=ParagraphsOnlyResponse)
def summarize_paragraphs(request: SummarizeRequest) -> ParagraphsOnlyResponse:
    """
    Summarize a block of text and return only per-paragraph summaries,
    without an aggregated document-level summary.
    """
    result = summarize_by_paragraphs(request.text)
    return ParagraphsOnlyResponse(paragraphs=result.get("paragraphs", []))


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    """
    Simple question-answering endpoint backed by Bedrock, optionally
    using caller-provided context.
    """
    answer = bedrock.answer_question(
        question=request.question,
        context=request.context,
    )
    return AskResponse(answer=answer)


@router.post("/questions", response_model=QuestionsResponse)
def generate_questions(request: QuestionsRequest) -> QuestionsResponse:
    """
    Generate follow-up questions for a given text, useful for exploring
    or indexing study materials.
    """
    questions = bedrock.generate_questions(
        text=request.text,
        count=request.count,
    )
    return QuestionsResponse(questions=questions)


