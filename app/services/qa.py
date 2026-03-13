from __future__ import annotations

from app.services import bedrock, opensearch


def answer_project_question(
    project_id: int,
    question: str,
    fallback_context: str | None = None,
) -> str:
    """
    Orchestrate a grounded Q&A flow for a given project.

    - Embed the user's question.
    - Retrieve similar documents for the project from OpenSearch.
    - Build a context string from retrieved documents.
    - Ask Bedrock to answer the question using that context, falling back
      to any caller-provided context if retrieval returns nothing.
    """
    # 1) Embed the question text
    query_embedding = bedrock.embed_text(question)
    if not query_embedding:
        # If we cannot embed (e.g. local dev without Bedrock), fall back
        # to a non-grounded answer using only the provided context.
        return bedrock.answer_question(question=question, context=fallback_context)

    # 2) Retrieve similar documents scoped to the project
    hits = opensearch.search_similar_documents(
        project_id=project_id,
        query_embedding=query_embedding,
    )

    # 3) Build context from the retrieved hits
    context_parts: list[str] = []
    for h in hits:
        text = h.get("text")
        if isinstance(text, str) and text.strip():
            context_parts.append(text)

    combined_context = "\n\n".join(context_parts).strip()
    if not combined_context:
        # No retrieved context; fall back to user-provided context if any.
        combined_context = fallback_context or ""

    # 4) Delegate to Bedrock for the actual answer generation
    return bedrock.answer_question(question=question, context=combined_context or None)

