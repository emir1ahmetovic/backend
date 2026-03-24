import json
import uuid

from sqlalchemy.orm import Session
from app.config import get_settings
from app.models.enums import ProcessingStatus, EmbeddingStatus, SummaryType
from app.models.material import Material, MaterialChunk
from app.models.summary import Summary, SummaryChunk
from app.services import bedrock, opensearch, textract
from app.services.summarization import summarize_by_paragraphs


def process_uploaded_material(material_id: uuid.UUID, db: Session) -> None:
    settings = get_settings()

    material: Material | None = db.get(Material, material_id)
    if material is None:
        return None

    material.processing_status = ProcessingStatus.PROCESSING
    db.commit()

    extracted_text = textract.extract_text_from_s3(
        s3_bucket=material.s3_bucket,
        s3_key=material.s3_key,
    )
    if not extracted_text:
        material.processing_status = ProcessingStatus.FAILED
        material.processing_error = "Extraction failed or empty text."
        db.commit()
        return None

    # Embedding via bedrock
    embedding = bedrock.embed_text(extracted_text)
    
    # Simple hash and token count
    chunk_hash = str(hash(extracted_text)) 
    token_count = len(extracted_text.split())

    # Create Material Chunk
    material_chunk = MaterialChunk(
        material_id=material.material_id,
        chunk_index=0,
        content=extracted_text,
        token_count=token_count,
        chunk_hash=chunk_hash,
        embedding_status=EmbeddingStatus.COMPLETED,
        embedding=embedding
    )
    db.add(material_chunk)
    db.flush() 

    # Keep OpenSearch in-sync as requested by User
    opensearch.index_document_embedding(
        project_id=str(material.project_id),
        document_id=str(material_chunk.material_chunk_id),
        embedding=embedding,
        text=extracted_text,
    )

    # Generate Summary
    summary_result = summarize_by_paragraphs(extracted_text)
    summary = Summary(
        project_id=material.project_id,
        created_by=material.uploaded_by,
        summary_title="Initial Material Summary",
        summary_content=json.dumps(summary_result),
        summary_type=SummaryType.DETAILED,
        ai_model="bedrock.default"
    )
    db.add(summary)
    db.flush()

    # Link Summary to Chunk
    summary_chunk = SummaryChunk(
        summary_id=summary.summary_id,
        chunk_id=material_chunk.material_chunk_id,
        relevance_score=1.0,
        chunk_order=0
    )
    db.add(summary_chunk)

    # Finalize Material
    material.processing_status = ProcessingStatus.COMPLETED
    material.total_chunks = 1
    material.total_tokens = token_count
    db.commit()
