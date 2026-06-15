import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app import main as main_module
from app.db import Base
from app.models import ContaminantRow, StateRow
from scripts.seed import load_contaminants, load_states


@pytest.fixture(scope="module")
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)
    with TestSession() as db:
        for c in load_contaminants():
            db.add(ContaminantRow.from_domain(c))
        for p in load_states():
            db.add(StateRow.from_domain(p))
        db.commit()
    main_module.SessionLocal = TestSession
    app = main_module.create_app()
    with TestClient(app) as c:
        yield c


def test_health(client):
    assert client.get("/api/health").json()["states"] >= 25


def test_states_list_has_severity(client):
    body = client.get("/api/states").json()
    assert body["count"] >= 25
    raj = next(s for s in body["states"] if s["state"] == "Rajasthan")
    assert raj["worst_severity"] == "severe"


def test_check_rajasthan(client):
    r = client.get("/api/check", params={"state": "Rajasthan"})
    assert r.status_code == 200
    body = r.json()
    assert body["overall_severity"] == "severe"
    assert body["risks"][0]["contaminant_id"] == "fluoride"
    assert body["boiling_warning"]


def test_check_by_state_code(client):
    r = client.get("/api/check", params={"state": "KA"})
    assert r.status_code == 200
    assert r.json()["state"] == "Karnataka"


def test_check_with_district_flag(client):
    r = client.get("/api/check", params={"state": "Telangana", "district": "Nalgonda"})
    body = r.json()
    assert body["risks"][0]["in_your_district"] is True


def test_unknown_state_404(client):
    r = client.get("/api/check", params={"state": "Atlantis"})
    assert r.status_code == 404
    assert r.json()["error"]["code"] == "not_found"


def test_clean_state_report(client):
    r = client.get("/api/check", params={"state": "Goa"})
    body = r.json()
    assert body["risks"] == []
    assert body["note"]


def test_stats(client):
    body = client.get("/api/stats").json()
    assert body["worst_fluoride_state"] == "Rajasthan"
    assert body["worst_arsenic_state"] == "West Bengal"
    assert "fluoride" in body["by_contaminant"]


def test_contaminants_reference(client):
    body = client.get("/api/contaminants").json()
    ids = {c["id"] for c in body["contaminants"]}
    assert {"arsenic", "fluoride", "nitrate", "uranium"} <= ids


def test_meta_disclaimer(client):
    assert client.get("/api/meta").json()["disclaimer"]
