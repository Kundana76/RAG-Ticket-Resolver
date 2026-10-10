import pytest


def process(client, text, confidence, tid=None):
    body = {"ticket_text": text, "confidence": confidence}
    if tid:
        body["ticket_id"] = tid
    return client.post("/copilot/process", json=body)


def test_root(client):
    assert client.get("/").json()["status"] == "running"


@pytest.mark.parametrize("conf,action", [
    (0.95, "auto_resolved"),
    (0.65, "draft_response"),
    (0.20, "escalated"),
])
def test_confidence_routing(client, conf, action):
    r = process(client, "Payment failed but money deducted", conf, tid=f"t-{action}")
    assert r.status_code == 200
    assert r.json()["action"] == action


def test_escalation_lands_in_queue(client, admin_headers):
    process(client, "Totally unclear weird problem", 0.1, tid="t-queue")
    q = client.get("/escalation/queue", headers=admin_headers).json()
    assert "t-queue" in str(q)


def test_queue_requires_login(client):
    assert client.get("/escalation/queue").status_code == 401


def test_metrics_endpoint(client):
    assert client.get("/metrics").status_code == 200
