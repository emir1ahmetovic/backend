import json

from sqlalchemy.orm import Session

from app.config import get_settings
from app.models.ai_output import AIOutput
from app.models.document import Document
from app.services import bedrock, opensearch, textract
from app.services.summarization import summarize_by_paragraphs


def process_uploaded_document(document_id: int, db: Session) -> None:
    """
    Background workflow to process an uploaded document:

    - Load the document row.
    - Extract text from S3 via Textract.
    - Summarize the text with Bedrock.
    - Generate an embedding and index it in OpenSearch.
    - Persist AI output and mark the document as processed.
    """
    settings = get_settings()

    document: Document | None = db.get(Document, document_id)
    if document is None:
        return None

    extracted_text = textract.extract_text_from_s3(
        s3_bucket=settings.s3_bucket_name,
        s3_key=document.s3_key,
    )
    if not extracted_text:
        document.status = "failed"
        db.add(document)
        db.commit()
        return None

    summary_result = summarize_by_paragraphs(extracted_text)
   
    embedding = bedrock.embed_text(extracted_text)

    opensearch.index_document_embedding(
        project_id=document.project_id,
        document_id=document.id,
        embedding=embedding,
        text=extracted_text,
    )

    ai_output = AIOutput(
        project_id=document.project_id,
        document_id=document.id,
        type="summary",
        content=json.dumps(summary_result),
    )
    db.add(ai_output)

    document.status = "processed"
    db.add(document)
    db.commit()