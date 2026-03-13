from fastapi.testclient import TestClient


def test_ai_summarize_smoke():
    from app.main import app

    client = TestClient(app)
    r = client.post(
        "/api/projects/1/summarize",
        json={"text": "hello"},
        headers={"Authorization": "Bearer dummy-token"},
    )
    assert r.status_code == 200
    assert "summary" in r.json()

