import pytest
from app.matching import normalize_name, find_matches
from app.models.college import College
from app.models.company import Company
from app.models.role import Role
from tests.helpers import register, make_admin, auth_headers


@pytest.fixture(autouse=True)
def seed(db_session):
    db_session.add(College(name="ABC University", city="Meerut", state="UP"))
    db_session.add(Company(name="Tata Consultancy Services"))
    db_session.add(Company(name="Infosys Limited"))
    db_session.flush()
    db_session.add(Role(company_id=1, title="Software Developer"))
    db_session.commit()


def test_normalization_and_aliases():
    assert normalize_name("Infosys Pvt. Ltd.") == "infosys"
    assert normalize_name("TCS") == normalize_name("Tata Consultancy Services")
    assert normalize_name("Ernst & Young") == "ernst and young"


def test_find_matches_scores_typos_and_word_order():
    class C:
        def __init__(self, id, name): self.id, self.name, self.normalized_name = id, name, normalize_name(name)
    cands = [C(1, "Infosys Limited"), C(2, "University of Delhi")]
    assert find_matches("Infosis Ltd", cands)[0]["id"] == 1
    assert find_matches("Delhi University of", cands, min_score=80)[0]["id"] == 2
    assert find_matches("Google", cands) == []


def test_submit_existing_company_reuses_it(client):
    tok = register(client, role="alumni", email="a@example.com")
    r = client.post("/api/companies/submit", json={"name": "TCS"}, headers=auth_headers(tok)).json()
    assert r["created"] is False and r["company"]["id"] == 1


def test_similar_name_asks_for_confirmation_then_creates_pending(client):
    tok = register(client, role="alumni", email="a@example.com")
    h = auth_headers(tok)
    r = client.post("/api/companies/submit", json={"name": "Infosis Ltd"}, headers=h).json()
    assert r["needs_confirmation"] is True and r["matches"][0]["name"] == "Infosys Limited"
    resp = client.post("/api/companies/submit", json={"name": "Infosis Ltd", "confirm_new": True}, headers=h)
    assert resp.status_code == 201
    company = resp.json()["company"]
    assert company["status"] == "pending"


def test_pending_company_visible_only_to_creator_and_admin(client, db_session):
    a1 = auth_headers(register(client, role="alumni", email="a1@example.com"))
    a2 = auth_headers(register(client, role="alumni", email="a2@example.com"))
    admin = auth_headers(make_admin(db_session, client))
    cid = client.post("/api/companies/submit", json={"name": "Zoho"}, headers=a1).json()["company"]["id"]

    names = lambda h: [c["name"] for c in client.get("/api/companies", headers=h).json()]
    assert "Zoho" in names(a1) and "Zoho" in names(admin)
    assert "Zoho" not in names(a2) and "Zoho" not in [c["name"] for c in client.get("/api/companies").json()]
    assert client.get(f"/api/companies/{cid}", headers=a2).status_code == 404
    assert client.post("/api/companies/submit", json={"name": "Zoho"}, headers=a2).status_code == 409


def test_student_cannot_submit_company(client):
    tok = register(client, email="s@example.com")
    assert client.post("/api/companies/submit", json={"name": "Zoho"}, headers=auth_headers(tok)).status_code == 403


def full_flow_payload(company_id, role_id):
    return {"company_id": company_id, "role_id": role_id, "college_id": 1, "placement_year": 2026, "rounds": []}


def test_experience_on_pending_company_cannot_be_approved_until_company_approved(client, db_session):
    a1 = auth_headers(register(client, role="alumni", email="a1@example.com"))
    a2 = auth_headers(register(client, role="alumni", email="a2@example.com"))
    admin = auth_headers(make_admin(db_session, client))
    cid = client.post("/api/companies/submit", json={"name": "Zoho"}, headers=a1).json()["company"]["id"]
    rid = client.post(f"/api/companies/{cid}/roles/submit", json={"title": "Backend Engineer"}, headers=a1).json()["role"]["id"]

    # someone else can't post against it; the creator can
    assert client.post("/api/experiences", json=full_flow_payload(cid, rid), headers=a2).status_code == 400
    exp = client.post("/api/experiences", json=full_flow_payload(cid, rid), headers=a1)
    assert exp.status_code == 201
    eid = exp.json()["id"]

    blocked = client.put(f"/api/experiences/{eid}/status", json={"status": "approved"}, headers=admin)
    assert blocked.status_code == 400

    sugg = client.get("/api/admin/suggestions", headers=admin).json()
    assert [c["name"] for c in sugg["companies"]] == ["Zoho"] and sugg["roles"][0]["title"] == "Backend Engineer"
    client.post(f"/api/admin/companies/{cid}/approve", headers=admin)
    client.post(f"/api/admin/roles/{rid}/approve", headers=admin)
    ok = client.put(f"/api/experiences/{eid}/status", json={"status": "approved"}, headers=admin)
    assert ok.status_code == 200
    assert "Zoho" in [c["name"] for c in client.get("/api/companies").json()]


def test_role_submit_reuses_exact_and_confirms_similar(client):
    h = auth_headers(register(client, role="alumni", email="a@example.com"))
    same = client.post("/api/companies/1/roles/submit", json={"title": "software  developer"}, headers=h).json()
    assert same["created"] is False and same["role"]["id"] == 1
    close = client.post("/api/companies/1/roles/submit", json={"title": "Software Developr"}, headers=h).json()
    assert close["needs_confirmation"] is True
    new = client.post("/api/companies/1/roles/submit", json={"title": "Data Analyst"}, headers=h)
    assert new.status_code == 201 and new.json()["role"]["status"] == "pending"


def test_admin_duplicates_and_merge(client, db_session):
    a1 = auth_headers(register(client, role="alumni", email="a1@example.com"))
    admin = auth_headers(make_admin(db_session, client))
    dup = client.post("/api/companies/submit", json={"name": "Infosis Ltd", "confirm_new": True}, headers=a1).json()["company"]
    rid = client.post(f"/api/companies/{dup['id']}/roles/submit", json={"title": "Software Developer"}, headers=a1).json()["role"]["id"]
    eid = client.post("/api/experiences", json=full_flow_payload(dup["id"], rid), headers=a1).json()["id"]
    assert client.get("/api/admin/suggestions", headers=admin).json()["companies"][0]["similar_to"]["name"] == "Infosys Limited"
    client.post(f"/api/admin/companies/{dup['id']}/approve", headers=admin)
    student = auth_headers(register(client, email="s@example.com"))
    for cid in (dup["id"], 2):  # student saved both spellings
        assert client.post("/api/bookmarks", json={"target_type": "company", "target_id": cid}, headers=student).status_code == 201

    pairs = client.get("/api/admin/duplicates", headers=admin).json()
    assert any({p["a"]["name"], p["b"]["name"]} == {"Infosys Limited", "Infosis Ltd"} for p in pairs)

    resp = client.post("/api/admin/companies/merge", json={"source_id": dup["id"], "target_id": 2}, headers=admin)
    assert resp.status_code == 200 and resp.json()["experiences_moved"] == 1

    exp = client.get(f"/api/experiences/{eid}", headers=a1).json()
    assert exp["company_id"] == 2 and exp["company_name"] == "Infosys Limited"
    assert exp["role_title"] == "Software Developer"
    detail = client.get("/api/companies/2", headers=admin).json()
    assert [r["title"] for r in detail["roles"]] == ["Software Developer"]
    assert client.get(f"/api/companies/{dup['id']}", headers=a1).status_code == 404
    saved = client.get("/api/bookmarks", headers=student).json()
    assert [b["target_id"] for b in saved] == [2]  # deduplicated onto the surviving company


def test_merge_validation_and_admin_only(client, db_session):
    admin = auth_headers(make_admin(db_session, client))
    student = auth_headers(register(client, email="s@example.com"))
    assert client.post("/api/admin/companies/merge", json={"source_id": 1, "target_id": 1}, headers=admin).status_code == 400
    assert client.post("/api/admin/companies/merge", json={"source_id": 1, "target_id": 99}, headers=admin).status_code == 404
    assert client.post("/api/admin/companies/merge", json={"source_id": 1, "target_id": 2}, headers=student).status_code == 403


def test_admin_create_company_blocks_normalized_duplicate(client, db_session):
    admin = auth_headers(make_admin(db_session, client))
    assert client.post("/api/companies", json={"name": "infosys pvt ltd"}, headers=admin).status_code == 409


def test_students_cannot_bookmark_pending_company(client, db_session):
    a1 = auth_headers(register(client, role="alumni", email="a1@example.com"))
    cid = client.post("/api/companies/submit", json={"name": "Zoho"}, headers=a1).json()["company"]["id"]
    student = auth_headers(register(client, email="s@example.com"))
    assert client.post("/api/bookmarks", json={"target_type": "company", "target_id": cid}, headers=student).status_code == 404
