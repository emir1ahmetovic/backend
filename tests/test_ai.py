from fastapi.testclient import TestClient
import uuid

def test_ai_summarize_smoke():
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/ai/summarize",
        json={"text": "hello"},
        headers={"Authorization": "Bearer dummy-token"},
    )
    assert r.status_code == 200
    assert "summary_content" in r.json()


def test_ai_ask_sse_events_no_context(monkeypatch):
    from app.main import app

    def fake_embed(_text: str):
        return []

    def fake_stream_answer_question(question: str, context: str | None = None):
        _ = (question, context)
        yield "Hello"
        yield " world"

    monkeypatch.setattr("app.services.bedrock.embed_text", fake_embed)
    monkeypatch.setattr("app.services.bedrock.stream_answer_question", fake_stream_answer_question)

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}
    payload = {"project_id": str(uuid.uuid4()), "question": "test?"}
    r = client.post("/api/ai/ask", json=payload, headers=headers)

    assert r.status_code == 200
    body = r.text
    assert "event: grounding" in body
    assert 'data: {"sources": []}' in body
    assert "event: token" in body
    assert 'data: "Hello"' in body
    assert 'data: " world"' in body
    assert "event: done" in body
    assert 'data: {"citations": []}' in body


def test_ai_ask_sse_grounding_and_citations(monkeypatch):
    from app.main import app
    from app.database import SessionLocal
    from app.models.chat import ChatMessage, ChatMessageChunk
    from app.models.user import User
    from app.models.project import Project
    from app.models.material import Material, MaterialChunk
    from app.models.enums import FileType, ProcessingStatus, EmbeddingStatus

    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    material_id = uuid.uuid4()
    chunk_id = uuid.uuid4()

    db = SessionLocal()
    db.add(
        User(
            user_id=user_id,
            email="sse-test@example.com",
            password_hash="x",
            first_name="SSE",
            last_name="Tester",
        )
    )
    db.add(
        Project(
            project_id=project_id,
            owner_id=user_id,
            project_name="P",
            project_description="D",
        )
    )
    db.add(
        Material(
            material_id=material_id,
            project_id=project_id,
            uploaded_by=user_id,
            original_file_name="notes.pdf",
            file_type=FileType.PDF,
            s3_bucket="b",
            s3_key="k",
            processing_status=ProcessingStatus.COMPLETED,
        )
    )
    db.add(
        MaterialChunk(
            material_chunk_id=chunk_id,
            material_id=material_id,
            chunk_index=0,
            content="FastAPI supports StreamingResponse for SSE",
            token_count=8,
            page_number=1,
            chunk_hash="h",
            embedding_status=EmbeddingStatus.COMPLETED,
        )
    )
    db.commit()
    db.close()

    def fake_embed(_text: str):
        return [0.1, 0.2]

    def fake_search(*, project_id: str, query_embedding: list[float], k: int = 5, chunk_ids=None):
        _ = (project_id, query_embedding, k, chunk_ids)
        return [
            {
                "opensearch_id": f"{project_id}:{chunk_id}",
                "retrieval_score": 0.91,
                "project_id": project_id,
                "document_id": str(chunk_id),
                "text": "FastAPI supports StreamingResponse for SSE",
            }
        ]

    def fake_stream_answer_question(question: str, context: str | None = None):
        _ = question
        assert context is not None
        yield "It supports SSE [S1]."

    monkeypatch.setattr("app.services.bedrock.embed_text", fake_embed)
    monkeypatch.setattr("app.services.opensearch.search_similar_documents", fake_search)
    monkeypatch.setattr("app.services.bedrock.stream_answer_question", fake_stream_answer_question)

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}
    payload = {"project_id": str(project_id), "question": "Does it stream?"}
    r = client.post("/api/ai/ask", json=payload, headers=headers)

    assert r.status_code == 200
    body = r.text
    assert "event: grounding" in body
    assert '"source_label": "S1"' in body
    assert '"filename": "notes.pdf"' in body
    assert '"retrieval_score": 0.91' in body
    assert "event: done" in body
    assert '"citations": [{"source_label": "S1"' in body

    db = SessionLocal()
    persisted_msg = db.query(ChatMessage).filter(ChatMessage.project_id == project_id).first()
    persisted_link = db.query(ChatMessageChunk).filter(ChatMessageChunk.chunk_id == chunk_id).first()
    db.close()
    assert persisted_msg is not None
    assert persisted_link is not None


def test_ai_ask_non_stream_json_mode(monkeypatch):
    from app.main import app

    def fake_embed(_text: str):
        return []

    def fake_stream_answer_question(question: str, context: str | None = None):
        _ = (question, context)
        yield "Alpha"
        yield "Beta"

    monkeypatch.setattr("app.services.bedrock.embed_text", fake_embed)
    monkeypatch.setattr("app.services.bedrock.stream_answer_question", fake_stream_answer_question)

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}
    payload = {"project_id": str(uuid.uuid4()), "question": "json mode?", "stream": False}
    r = client.post("/api/ai/ask", json=payload, headers=headers)

    assert r.status_code == 200
    data = r.json()
    assert data["answer"] == "AlphaBeta"
    assert data["citations"] == []
    assert data["grounding_context"] == []


def test_ai_ask_selected_material_filters_chunks(monkeypatch):
    from app.main import app
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.project import Project
    from app.models.material import Material, MaterialChunk
    from app.models.enums import FileType, ProcessingStatus, EmbeddingStatus

    project_id = uuid.uuid4()
    user_id = uuid.uuid4()
    material_a = uuid.uuid4()
    material_b = uuid.uuid4()
    chunk_a = uuid.uuid4()
    chunk_b = uuid.uuid4()

    db = SessionLocal()
    db.add(User(user_id=user_id, email="filter-test@example.com", password_hash="x", first_name="F", last_name="T"))
    db.add(Project(project_id=project_id, owner_id=user_id, project_name="P", project_description="D"))
    db.add(Material(material_id=material_a, project_id=project_id, uploaded_by=user_id, original_file_name="a.pdf", file_type=FileType.PDF, s3_bucket="b", s3_key="a", processing_status=ProcessingStatus.COMPLETED))
    db.add(Material(material_id=material_b, project_id=project_id, uploaded_by=user_id, original_file_name="b.pdf", file_type=FileType.PDF, s3_bucket="b", s3_key="b", processing_status=ProcessingStatus.COMPLETED))
    db.add(MaterialChunk(material_chunk_id=chunk_a, material_id=material_a, chunk_index=0, content="A", token_count=1, chunk_hash="ha", embedding_status=EmbeddingStatus.COMPLETED))
    db.add(MaterialChunk(material_chunk_id=chunk_b, material_id=material_b, chunk_index=0, content="B", token_count=1, chunk_hash="hb", embedding_status=EmbeddingStatus.COMPLETED))
    db.commit()
    db.close()

    seen = {"chunk_ids": None}

    def fake_embed(_text: str):
        return [0.1]

    def fake_search(*, project_id: str, query_embedding: list[float], k: int = 5, chunk_ids=None):
        _ = (project_id, query_embedding, k)
        seen["chunk_ids"] = chunk_ids
        return []

    monkeypatch.setattr("app.services.bedrock.embed_text", fake_embed)
    monkeypatch.setattr("app.services.opensearch.search_similar_documents", fake_search)

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}
    payload = {
        "project_id": str(project_id),
        "question": "filter?",
        "selected_material_ids": [str(material_a)],
    }
    r = client.post("/api/ai/ask", json=payload, headers=headers)
    assert r.status_code == 200
    assert seen["chunk_ids"] == [f"{project_id}:{chunk_a}"]