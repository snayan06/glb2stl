from fastapi.testclient import TestClient
from glb2stl.app import app

client = TestClient(app)

def test_liveness():
    r = client.get("/health/liveness")
    assert r.status_code == 200
    assert r.json()["status"] == "alive"

def test_readiness():
    r = client.get("/health/readiness")
    assert r.status_code == 200
    assert r.json()["status"] in {"ready", "not_ready"}
