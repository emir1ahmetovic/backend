from fastapi.testclient import TestClient


def test_documents_smoke():
    from app.main import app

    client = TestClient(app)
    r = client.get("/api/projects/1/documents", headers={"Authorization": "Bearer dummy-token"})
    assert r.status_code == 200
    assert r.json() == []

