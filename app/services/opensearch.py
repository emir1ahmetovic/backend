from __future__ import annotations

from typing import Any

from app.config import get_settings


def _get_client():
    """
    Lazily construct an OpenSearch client.

    Returns None if opensearch-py is not available so that the rest of the
    application can continue to function in local/dev environments.
    """
    settings = get_settings()
    try:
        from opensearchpy import OpenSearch  
    except Exception:  
        return None

    return OpenSearch(hosts=[settings.opensearch_endpoint])


def index_document_embedding(
    project_id: int,
    document_id: int,
    embedding: list[float],
    text: str,
) -> None:
    """
    Index a document's embedding and raw text for later semantic search.
    """
    client = _get_client()
    if client is None or not embedding:
        return None

    body: dict[str, Any] = {
        "project_id": project_id,
        "document_id": document_id,
        "embedding": embedding,
        "text": text,
    }

    try:
        client.index(index="documents", id=f"{project_id}:{document_id}", body=body)
    except Exception:
        return None


def search_similar_documents(
    project_id: int,
    query_embedding: list[float],
    k: int = 5,
) -> list[dict]:
    """
    Perform a k-NN search in OpenSearch for documents similar to the query.

    Returns a list of hit dicts with at least a \"text\" field when possible.
    """
    client = _get_client()
    if client is None or not query_embedding:
        return []

    body: dict[str, Any] = {
        "size": k,
        "query": {
            "bool": {
                "must": [
                    {
                        "knn": {
                            "embedding": {
                                "vector": query_embedding,
                                "k": k,
                            }
                        }
                    }
                ],
                "filter": [
                    {"term": {"project_id": project_id}},
                ],
            }
        },
    }

    try:
        resp = client.search(index="documents", body=body)
    except Exception:
        return []

    hits = (resp.get("hits") or {}).get("hits") or []
    results: list[dict] = []
    for h in hits:
        source = h.get("_source") or {}
        if not isinstance(source, dict):
            continue
        results.append(source)

    return results