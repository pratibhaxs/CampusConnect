import pytest
from app.models.college import College
from app.models.company import Company
from app.models.role import Role
from tests.helpers import register, make_admin, auth_headers


@pytest.fixture(autouse=True)
def seed(db_session):
    db_session.add(College(name="ABC University", city="Meerut", state="UP"))
    company = Company(name="XYZ Technologies")
    db_session.add(company)
    db_session.flush()
    db_session.add(Role(company_id=company.id, title="Software Developer"))
    db_session.commit()


def setup_author(client, admin_tok):
    alumni_tok = register(client, role="alumni", email="alumni@example.com")
    payload = {"company_id": 1, "role_id": 1, "college_id": 1, "placement_year": 2026,
               "rounds": [{"round_number": 1, "round_type": "Coding", "difficulty": "easy",
                           "questions": [{"question_text": "Reverse a linked list", "topic": "DSA"}]}]}
    exp_id = client.post("/api/experiences", json=payload, headers=auth_headers(alumni_tok)).json()["id"]
    client.put(f"/api/experiences/{exp_id}/status", json={"status": "approved"}, headers=auth_headers(admin_tok))
    return exp_id


def test_deleting_author_keeps_experience_anonymized(client, db_session):
    admin_tok = make_admin(db_session, client)
    exp_id = setup_author(client, admin_tok)
    resp = client.delete("/api/admin/users/2", headers=auth_headers(admin_tok))
    assert resp.status_code == 200
    assert resp.json()["experiences_anonymized"] == 1

    exp = client.get(f"/api/experiences/{exp_id}").json()
    assert exp["user_name"] == "Anonymous alumnus"
    assert exp["user_id"] is None
    assert len(exp["rounds"]) == 1


def test_deleting_user_removes_bookmarks_and_votes_but_keeps_reports(client, db_session):
    admin_tok = make_admin(db_session, client)
    exp_id = setup_author(client, admin_tok)
    student_tok = register(client, email="student@example.com")
    h = auth_headers(student_tok)
    client.post("/api/bookmarks", json={"target_type": "experience", "target_id": exp_id}, headers=h)
    client.post(f"/api/experiences/{exp_id}/helpful", headers=h)
    client.post("/api/reports", json={"experience_id": exp_id, "reason": "spam"}, headers=h)

    assert client.delete("/api/admin/users/3", headers=auth_headers(admin_tok)).status_code == 200
    assert client.get(f"/api/experiences/{exp_id}").json()["helpful_count"] == 0
    reports = client.get("/api/reports", headers=auth_headers(admin_tok)).json()
    assert len(reports) == 1 and reports[0]["reporter_name"] == "Deleted user"


def test_admin_cannot_delete_self_or_missing_user_and_non_admin_forbidden(client, db_session):
    admin_tok = make_admin(db_session, client)
    student_tok = register(client, email="student@example.com")
    assert client.delete("/api/admin/users/1", headers=auth_headers(admin_tok)).status_code == 400
    assert client.delete("/api/admin/users/999", headers=auth_headers(admin_tok)).status_code == 404
    assert client.delete("/api/admin/users/1", headers=auth_headers(student_tok)).status_code == 403


def test_admin_cannot_delete_another_admin(client, db_session):
    admin_tok = make_admin(db_session, client)
    make_admin(db_session, client, email="admin2@example.com")
    assert client.delete("/api/admin/users/2", headers=auth_headers(admin_tok)).status_code == 400


def test_admin_user_list_with_filters_and_counts(client, db_session):
    admin_tok = make_admin(db_session, client)
    setup_author(client, admin_tok)
    register(client, email="student@example.com")
    h = auth_headers(admin_tok)
    users = client.get("/api/admin/users", headers=h).json()
    assert len(users) == 3
    alumni = next(u for u in users if u["role"] == "alumni")
    assert alumni["experience_count"] == 1
    assert [u["role"] for u in client.get("/api/admin/users?role=student", headers=h).json()] == ["student"]
    assert len(client.get("/api/admin/users?q=ALUMNI", headers=h).json()) == 1
    assert client.get("/api/admin/users", headers=auth_headers(register(client, email="x@example.com"))).status_code == 403


def test_user_can_delete_own_account_with_password(client, db_session):
    admin_tok = make_admin(db_session, client)
    exp_id = setup_author(client, admin_tok)
    h = auth_headers(login_token(client, "alumni@example.com"))
    assert client.request("DELETE", "/api/auth/me", json={"password": "wrong"}, headers=h).status_code == 400
    resp = client.request("DELETE", "/api/auth/me", json={"password": "secret123"}, headers=h)
    assert resp.status_code == 200 and resp.json()["experiences_anonymized"] == 1
    assert client.get(f"/api/experiences/{exp_id}").json()["user_name"] == "Anonymous alumnus"
    assert client.post("/api/auth/login", json={"email": "alumni@example.com", "password": "secret123"}).status_code == 401
    # the old token no longer works
    assert client.get("/api/auth/me", headers=h).status_code in (401, 404)


def test_admin_cannot_use_self_delete_endpoint(client, db_session):
    admin_tok = make_admin(db_session, client)
    resp = client.request("DELETE", "/api/auth/me", json={"password": "secret123"}, headers=auth_headers(admin_tok))
    assert resp.status_code == 403


def login_token(client, email):
    return client.post("/api/auth/login", json={"email": email, "password": "secret123"}).json()["token"]
