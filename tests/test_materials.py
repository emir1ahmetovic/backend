from fastapi.testclient import TestClient
import uuid


def test_materials_crud_flow():
    from app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}

    # create a project to attach materials
    project_data = {
        "project_name": "Material project",
        "project_description": "for materials",
    }
    r = client.post("/api/projects", json=project_data, headers=headers)
    assert r.status_code == 200
    project_id = r.json()["project_id"]

    # fetch materials initially empty
    r = client.get(f"/api/projects/{project_id}/materials", headers=headers)
    assert r.status_code == 200
    assert r.json() == []

    # create material
    material_payload = {
        "original_file_name": "test.pdf",
        "file_type": "pdf",
        "s3_bucket": "test-bucket",
        "s3_key": "test-key",
    }
    r = client.post(
        f"/api/projects/{project_id}/materials",
        json=material_payload,
        headers=headers,
    )
    assert r.status_code == 200
    material = r.json()
    assert material["project_id"] == project_id
    assert material["original_file_name"] == "test.pdf"
    assert material["material_id"]

    # list materials now contains one entry
    r = client.get(f"/api/projects/{project_id}/materials", headers=headers)
    assert r.status_code == 200
    assert len(r.json()) == 1

    # delete material
    r = client.delete(f"/api/projects/{project_id}/materials/{material['material_id']}", headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True

    r = client.get(f"/api/projects/{project_id}/materials", headers=headers)
    assert r.status_code == 200
    assert r.json() == []
