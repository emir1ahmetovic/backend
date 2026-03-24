from __future__ import annotations

import json
import uuid
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.models.chat import ChatMessage, ChatMessageChunk
from app.models.enums import MessageRole
from app.models.material import Material, MaterialChunk
from app.models.project import Project
from app.services import bedrock, opensearch


def _sse_event(event: str, data: dict | str) -> str:
    payload = json.dumps(data)
    return f"event: {event}\ndata: {payload}\n\n"


def answer_project_question(
    project_id: str,
    question: str,
    db: Session,
    user_id: str | None = None,
    selected_material_ids: list[str] | None = None,
    fallback_context: str | None = None,
):
    user_uuid = uuid.UUID(user_id) if user_id else None
    project_uuid = uuid.UUID(project_id)
    if user_uuid is None:
        owner_id = db.execute(
            select(Project.owner_id).where(Project.project_id == project_uuid)
        ).scalar_one_or_none()
        if owner_id:
            user_uuid = owner_id
    query_embedding = bedrock.embed_text(question)

    chunk_ids_to_search = None
    if selected_material_ids:
        selected_uuid_ids = []
        for material_id in selected_material_ids:
            try:
                selected_uuid_ids.append(uuid.UUID(material_id))
            except ValueError:
                continue
        stmt = select(MaterialChunk.material_chunk_id).where(
            MaterialChunk.material_id.in_(selected_uuid_ids)
        )
        result = db.execute(stmt).scalars().all()
        chunk_ids_to_search = [f"{project_id}:{str(cid)}" for cid in result]

    if not query_embedding:
        fallback_chat: ChatMessage | None = None
        if user_uuid:
            fallback_chat = ChatMessage(
                chat_id=uuid.uuid4(),
                project_id=project_uuid,
                created_by=user_uuid,
                role=MessageRole.ASSISTANT,
                content="",
                token_count=0,
            )
            db.add(fallback_chat)
            db.commit()

        def _fallback_stream():
            yield _sse_event("grounding", {"sources": []})
            answer_parts: list[str] = []
            for token in bedrock.stream_answer_question(question=question, context=fallback_context):
                answer_parts.append(token)
                yield _sse_event("token", token)
            yield _sse_event("done", {"citations": []})
            if fallback_chat is not None:
                fallback_chat.content = "".join(answer_parts)
                fallback_chat.token_count = len(fallback_chat.content.split())
                db.add(fallback_chat)
                db.commit()
        return _fallback_stream()

    hits = opensearch.search_similar_documents(
        project_id=project_id,
        query_embedding=query_embedding,
        chunk_ids=chunk_ids_to_search,
    )

    hit_chunk_ids: list[uuid.UUID] = []
    for h in hits:
        doc_id = h.get("document_id")
        try:
            if doc_id:
                hit_chunk_ids.append(uuid.UUID(str(doc_id)))
        except ValueError:
            continue

    metadata_by_chunk: dict[str, dict] = {}
    if hit_chunk_ids:
        chunk_stmt = (
            select(
                MaterialChunk.material_chunk_id,
                MaterialChunk.material_id,
                MaterialChunk.chunk_index,
                MaterialChunk.page_number,
                MaterialChunk.slide_number,
                MaterialChunk.section_heading,
                Material.original_file_name,
            )
            .join(Material, Material.material_id == MaterialChunk.material_id)
            .where(MaterialChunk.material_chunk_id.in_(hit_chunk_ids))
        )
        for row in db.execute(chunk_stmt).all():
            metadata_by_chunk[str(row.material_chunk_id)] = {
                "material_id": row.material_id,
                "chunk_index": row.chunk_index,
                "page_number": row.page_number,
                "slide_number": row.slide_number,
                "section_heading": row.section_heading,
                "filename": row.original_file_name,
            }

    context_parts: list[str] = []
    sources: list[dict] = []
    for rank, h in enumerate(hits, start=1):
        text = h.get("text")
        if isinstance(text, str) and text.strip():
            source_label = f"S{rank}"
            context_parts.append(f"[{source_label}]\n{text.strip()}")

            doc_id = str(h.get("document_id") or "")
            item_meta = metadata_by_chunk.get(doc_id, {})
            source = {
                "source_label": source_label,
                "chunk_id": doc_id,
                "material_id": str(item_meta["material_id"]) if item_meta.get("material_id") else None,
                "filename": item_meta.get("filename"),
                "chunk_index": item_meta.get("chunk_index"),
                "page_number": item_meta.get("page_number"),
                "slide_number": item_meta.get("slide_number"),
                "section_heading": item_meta.get("section_heading"),
                "retrieval_score": h.get("retrieval_score"),
                "rank": rank,
                "excerpt": text.strip()[:240],
            }
            sources.append(source)

    combined_context = "\n\n".join(context_parts).strip()
    if not combined_context:
        combined_context = fallback_context or ""

    chat_message: ChatMessage | None = None
    if user_uuid:
        chat_message = ChatMessage(
            chat_id=uuid.uuid4(),
            project_id=project_uuid,
            created_by=user_uuid,
            role=MessageRole.ASSISTANT,
            content="",
            token_count=0,
        )
        db.add(chat_message)
        db.flush()

        for source in sources:
            chunk_id = source.get("chunk_id")
            if not chunk_id:
                continue
            try:
                db.add(
                    ChatMessageChunk(
                        chat_id=chat_message.chat_id,
                        chunk_id=uuid.UUID(chunk_id),
                        relevance_score=int((source.get("retrieval_score") or 0) * 1000),
                        was_used_in_prompt=True,
                        chunk_order=source.get("rank") or 0,
                    )
                )
            except ValueError:
                continue
        db.commit()

    def _stream():
        yield _sse_event("grounding", {"sources": sources})
        full_answer_parts: list[str] = []
        for token in bedrock.stream_answer_question(question=question, context=combined_context or None):
            full_answer_parts.append(token)
            yield _sse_event("token", token)
        answer_text = "".join(full_answer_parts)

        used_labels = {f"S{n}" for n in range(1, len(sources) + 1) if f"[S{n}]" in answer_text}
        citations = [s for s in sources if s["source_label"] in used_labels]
        yield _sse_event("done", {"citations": citations})

        if chat_message is not None:
            chat_message.content = answer_text
            chat_message.token_count = len(answer_text.split())
            db.add(chat_message)
            db.commit()

    return _stream()

