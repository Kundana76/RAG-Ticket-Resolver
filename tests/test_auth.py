from copilot.auth import issue_token, verify_token, hash_password, verify_password


def test_password_roundtrip():
    h = hash_password("hunter2-hunter2")
    assert verify_password("hunter2-hunter2", h)
    assert not verify_password("wrong", h)


def test_token_roundtrip_and_tamper():
    t = issue_token("kanna", "agent")
    assert verify_token(t) == {"username": "kanna", "role": "agent"}
    payload, sig = t.split(".")
    assert verify_token(payload + "." + sig[::-1]) is None
    assert verify_token("garbage") is None


def test_expired_token():
    assert verify_token(issue_token("kanna", "agent", ttl=-5)) is None


def test_first_register_is_admin_then_locked(client, admin_headers):
    # admin_headers already created the first account
    me = client.get("/auth/me", headers=admin_headers).json()
    assert me["role"] == "admin"
    # a stranger can no longer self-register
    r = client.post("/auth/register", json={"username": "intruder", "password": "password123"})
    assert r.status_code == 403


def test_admin_adds_agent_and_agent_cannot_reset(client, admin_headers):
    r = client.post("/auth/register", headers=admin_headers,
                    json={"username": "agent1", "password": "password123", "role": "agent"})
    assert r.status_code == 200
    login = client.post("/auth/login", json={"username": "agent1", "password": "password123"})
    assert login.status_code == 200
    agent = {"Authorization": f"Bearer {login.json()['token']}"}
    assert client.get("/auth/me", headers=agent).json()["role"] == "agent"
    assert client.post("/demo/reset", headers=agent).status_code == 403
    assert client.post("/demo/reset", headers=admin_headers).status_code == 200


def test_bad_login_and_weak_password(client, admin_headers):
    assert client.post("/auth/login", json={"username": "boss", "password": "nope"}).status_code == 401
    r = client.post("/auth/register", headers=admin_headers,
                    json={"username": "weak", "password": "short"})
    assert r.status_code == 400


def test_claim_uses_signed_in_name_and_resolve(client, admin_headers):
    client.post("/copilot/process", json={"ticket_text": "Mystery outage nobody understands",
                                          "confidence": 0.05, "ticket_id": "t-claim"})
    assert client.post("/escalation/claim", json={}).status_code == 401
    r = client.post("/escalation/claim", json={"agent_name": "someone-else"}, headers=admin_headers)
    assert r.status_code == 200
    assert r.json()["assigned_to"] == "boss"
    tid = r.json()["ticket_id"]
    r = client.post("/escalation/resolve", headers=admin_headers,
                    json={"ticket_id": tid, "resolution_note": "restarted the thing"})
    assert r.json()["resolved_by"] == "boss"
