from fastapi.testclient import TestClient


def test_project_crud_flow():
    from app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}

    # initial list is empty
    r = client.get("/api/projects", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    # create project
    project_payload = {
        "project_name": "Test Project",
        "project_description": "Test description",
    }
    r = client.post("/api/projects", json=project_payload, headers=headers)
    assert r.status_code == 200
    project = r.json()
    assert project["project_name"] == "Test Project"
    assert project["project_description"] == "Test description"
    assert project["project_id"]
    assert project["owner_id"]

    # list includes created project
    r = client.get("/api/projects", headers=headers)
    assert r.status_code == 200
    projects = r.json()
    assert len(projects) == 1
    assert projects[0]["project_id"] == project["project_id"]

    # delete project
    r = client.delete(f"/api/projects/{project['project_id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    # no active projects after soft delete
    r = client.get("/api/projects", headers=headers)
    assert r.status_code == 200
    assert r.json() == []