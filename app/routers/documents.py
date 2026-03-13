from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user
from app.models.document import Document
from app.config import get_settings
from app.services import s3
from app.schemas.document import DocumentCreate, DocumentRead
from app.tasks.document_tasks import process_uploaded_document


router = APIRouter(prefix="/api/projects/{project_id}/documents", tags=["documents"])


@router.get("/", response_model=list[DocumentRead])
def list_documents(
    project_id: int,
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[DocumentRead]:
    docs = (
        db.query(Document)
        .filter(Document.project_id == project_id)
        .order_by(Document.created_at.desc())
        .all()
    )
    return [
        DocumentRead(
            id=d.id,
            project_id=d.project_id,
            filename=d.filename,
            s3_key=d.s3_key,
            status=d.status,
        )
        for d in docs
    ]


@router.post("/", response_model=DocumentRead)
def create_document(
    project_id: int,
    payload: DocumentCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    _user: dict = Depends(get_current_user),
) -> DocumentRead:
    # Persist the document metadata first so that the background task
    # has a stable primary key to work with.
    doc = Document(
        project_id=project_id,
        filename=payload.filename,
        s3_key=payload.s3_key,
        status="queued",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    background_tasks.add_task(process_uploaded_document, doc.id, db)

    return DocumentRead(
        id=doc.id,
        project_id=doc.project_id,
        filename=doc.filename,
        s3_key=doc.s3_key,
        status=doc.status,
    )


@router.delete("/{document_id}")
def delete_document(
    project_id: int,
    document_id: int,
    _user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    settings = get_settings()

    doc: Document | None = db.get(Document, document_id)
    if doc is None or doc.project_id != project_id:
        return {"ok": False, "project_id": project_id, "deleted_document_id": None}

    # Best-effort delete from S3; ignore failures for now.
    s3.delete_file(bucket=settings.s3_bucket_name, key=doc.s3_key)

    db.delete(doc)
    db.commit()

    return {"ok": True, "project_id": project_id, "deleted_document_id": document_id}

