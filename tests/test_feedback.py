from copilot.feedback import compute_adjustment, MIN_VOTES, MAX_SWING


def test_no_effect_below_min_votes():
    assert compute_adjustment(MIN_VOTES - 1, 0) == 0.0


def test_adjustment_is_bounded_and_signed():
    assert 0 < compute_adjustment(50, 0) <= MAX_SWING
    assert -MAX_SWING <= compute_adjustment(0, 50) < 0
    assert compute_adjustment(10, 10) == 0.0


def vote(client, tid, title, helpful):
    return client.post("/feedback", json={"ticket_id": tid, "article_title": title, "helpful": helpful})


def test_vote_counts_and_one_vote_per_ticket(client):
    title = "Feedback Test Article A"
    assert vote(client, "fb-1", title, True).json()["helpful_votes"] == 1
    # same ticket voting again the same way changes nothing
    again = vote(client, "fb-1", title, True).json()
    assert again["helpful_votes"] == 1 and again["changed"] is False
    # changing their mind moves the vote instead of adding one
    flipped = vote(client, "fb-1", title, False).json()
    assert flipped["helpful_votes"] == 0 and flipped["unhelpful_votes"] == 1


def test_enough_votes_move_the_ranking_signal(client):
    title = "Feedback Test Article B"
    for i in range(6):
        last = vote(client, f"fb-b-{i}", title, True).json()
    assert last["helpful_votes"] == 6
    assert last["adjustment"] > 0
    stats = client.get("/feedback/stats").json()
    assert any(a["article_title"] == title for a in stats["articles"])


def test_feedback_validation(client):
    r = client.post("/feedback", json={"ticket_id": "", "article_title": "x", "helpful": True})
    assert r.status_code == 422


def test_feedback_reranks_live_recommendations(client):
    text = "Refund has not arrived after cancellation"
    first = client.post("/recommend", json={"ticket_text": text}).json()["recommendations"]
    top, runner_up = first[0]["article_title"], first[1]["article_title"]
    # many people say the runner-up was the helpful one and the top pick was not
    for i in range(12):
        vote(client, f"rr-{i}", runner_up, True)
        vote(client, f"rr-{i}", top, False)
    after = client.post("/recommend", json={"ticket_text": text}).json()["recommendations"]
    by_title = {r["article_title"]: r for r in after}
    assert by_title[runner_up]["feedback_adjustment"] > 0
    assert by_title[top]["feedback_adjustment"] < 0
    # bounded: never moves a score by more than the cap
    assert abs(by_title[top]["score"] - by_title[top]["raw_score"]) <= 0.1001
