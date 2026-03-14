from __future__ import annotations

from app.services import bedrock, opensearch


def answer_project_question(
    project_id: int,
    question: str,
    fallback_context: str | None = None,
) -> str:
   
    query_embedding = bedrock.embed_text(question)
    if not query_embedding:
       
        return bedrock.answer_question(question=question, context=fallback_context)
  
    hits = opensearch.search_similar_documents(
        project_id=project_id,
        query_embedding=query_embedding,
    )

    context_parts: list[str] = []
    for h in hits:
        text = h.get("text")
        if isinstance(text, str) and text.strip():
            context_parts.append(text)

    combined_context = "\n\n".join(context_parts).strip()
    if not combined_context:

        combined_context = fallback_context or ""

    return bedrock.answer_question(question=question, context=combined_context or None)

