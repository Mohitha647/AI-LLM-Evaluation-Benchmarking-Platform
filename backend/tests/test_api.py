import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ["DATABASE_URL"] = "sqlite:///./test_arena.db"
os.environ["MOCK_MODE"] = "true"

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_list_models():
    resp = client.get("/models")
    assert resp.status_code == 200
    assert len(resp.json()["models"]) >= 2


def test_battle_and_vote_flow():
    resp = client.post("/battle", json={"prompt": "Explain recursion simply."})
    assert resp.status_code == 200
    data = resp.json()
    assert data["model_a"] != data["model_b"]
    battle_id = data["battle_id"]

    vote_resp = client.post("/vote", json={"battle_id": battle_id, "choice": "a"})
    assert vote_resp.status_code == 200
    assert vote_resp.json()["winner"] == "a"

    # duplicate vote on the same battle should be rejected
    dup_resp = client.post("/vote", json={"battle_id": battle_id, "choice": "b"})
    assert dup_resp.status_code == 409


def test_leaderboard():
    resp = client.get("/leaderboard")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


def test_empty_prompt_rejected():
    resp = client.post("/battle", json={"prompt": "   "})
    assert resp.status_code == 400
