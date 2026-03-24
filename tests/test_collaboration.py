from fastapi.testclient import TestClient


def test_collaboration_invite_and_remove():
    from app.main import app

    client = TestClient(app)
    headers = {"Authorization": "Bearer dummy-token"}

    project_payload = {
        "project_name": "Collab Project",
        "project_description": "for collaboration",
    }
    r = client.post("/api/projects", json=project_payload, headers=headers)
    assert r.status_code == 200
    project_id = r.json()["project_id"]

    # create target user in database by switching token
    user_headers = {"Authorization": "Bearer other-token"}
    r = client.get("/api/projects", headers=user_headers)
    assert r.status_code == 200

    # add member by email (from other-token user)
    target_email = "user-other-token@example.com"
    member_payload = {
        "email": target_email,
        "role": "viewer",
    }
    r = client.post(
        f"/api/projects/{project_id}/members",
        json=member_payload,
        headers=headers,
    )
    assert r.status_code == 200
    assert r.json()["email"] == target_email

    member_id = r.json()["project_member_id"]

    # remove the member
    r = client.delete(f"/api/projects/{project_id}/members/{member_id}", headers=headers)
    assert r.status_code == 200
    assert r.json()["ok"] is True