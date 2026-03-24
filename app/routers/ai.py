from __future__ import annotations

import json
import uuid
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.enums import SummaryType, DifficultyLevel

from app.schemas.ai import (
    AskRequest,
    AskResponse,
    QuestionsRequest,
    QuestionsResponse,
    QuestionRead,
    SummarizeRequest,
    SummaryRead,
)
from app.services import bedrock, qa
from app.services.summarization import summarize_by_paragraphs

router = APIRouter(prefix="/api/ai", tags=["ai"])

@router.post("/summarize", response_model=SummaryRead)
def summarize(request: SummarizeRequest) -> SummaryRead:
    result = summarize_by_paragraphs(request.text)
    
    return SummaryRead(
        summary_id=uuid.uuid4(),
        summary_title="Auto-Generated Summary",
        summary_content=str(result),
        summary_type=request.summary_type
    )

@router.post("/ask")
def ask(
    request: AskRequest,
    db: Session = Depends(get_db),
):
    selected_ids = [str(i) for i in request.selected_material_ids] if request.selected_material_ids else None
    generator = qa.answer_project_question(
        project_id=str(request.project_id),
        question=request.question,
        db=db,
        selected_material_ids=selected_ids,
    )
    if not request.stream:
        answer_parts: list[str] = []
        citations: list[dict] = []
        grounding_context: list[dict] = []
        for chunk in generator:
            if not isinstance(chunk, str):
                continue
            event_type = None
            data_payload = None
            for line in chunk.splitlines():
                if line.startswith("event: "):
                    event_type = line.removeprefix("event: ").strip()
                if line.startswith("data: "):
                    data_payload = line.removeprefix("data: ").strip()
            if event_type == "token" and data_payload is not None:
                try:
                    token = json.loads(data_payload)
                except json.JSONDecodeError:
                    token = data_payload
                if isinstance(token, str):
                    answer_parts.append(token)
            elif event_type == "grounding" and data_payload:
                try:
                    grounding_context = (json.loads(data_payload) or {}).get("sources") or []
                except json.JSONDecodeError:
                    grounding_context = []
            elif event_type == "done" and data_payload:
                try:
                    citations = (json.loads(data_payload) or {}).get("citations") or []
                except json.JSONDecodeError:
                    citations = []

        return AskResponse(
            answer="".join(answer_parts),
            citations=citations,
            grounding_context=grounding_context,
        )
    return StreamingResponse(generator, media_type="text/event-stream")

@router.post("/questions", response_model=QuestionsResponse)
def generate_questions(request: QuestionsRequest) -> QuestionsResponse:
    questions_strs = bedrock.generate_questions(
        text=request.text,
        count=request.count,
    )
    q_reads = [
        QuestionRead(
            question_id=uuid.uuid4(), 
            question_text=q, 
            difficulty_level=request.difficulty
        ) for q in questions_strs
    ]
    return QuestionsResponse(questions=q_reads)
