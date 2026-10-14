from tests.conftest import auth_headers

PROFILE = {
    "experience_level": "intermediate",
    "training_goal": "muscle",
    "days_per_week": 4,
    "session_minutes": 60,
    "equipment": "gym",
    "birth_year": 1995,
    "height_cm": 182,
    "weight_kg": 80.5,
}


def save_profile(client, headers, **changes):
    return client.put("/api/v1/me/fitness", json={**PROFILE, **changes}, headers=headers)


def test_profile_is_empty_then_saved_and_updated(client):  # US-08
    me = auth_headers(client)
    assert client.get("/api/v1/me/fitness", headers=me).json() is None
    res = save_profile(client, me)
    assert res.status_code == 200
    assert res.json()["weight_kg"] == 80.5
    save_profile(client, me, training_goal="strength", weight_kg=None)
    body = client.get("/api/v1/me/fitness", headers=me).json()
    assert (body["training_goal"], body["weight_kg"]) == ("strength", None)


def test_profile_validation(client):
    me = auth_headers(client)
    res = save_profile(client, me, days_per_week=7, height_cm=20, training_goal="fly", weight_kg=-5)
    assert res.status_code == 422
    fields = {d["field"] for d in res.json()["error"]["details"]}
    assert fields == {"days_per_week", "height_cm", "training_goal", "weight_kg"}


def test_plan_needs_a_profile(client):
    me = auth_headers(client)
    res = client.post("/api/v1/training-plans", headers=me)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "fitness_profile_required"


def test_generated_plan_has_days_exercises_sets_reps_and_rest(client):  # US-09, FIT-05
    me = auth_headers(client)
    save_profile(client, me)
    res = client.post("/api/v1/training-plans", headers=me)
    assert res.status_code == 201
    plan = res.json()
    assert (plan["version"], plan["status"]) == (1, "draft")
    assert plan["goal_snapshot"]["training_goal"] == "muscle"
    assert [d["name"] for d in plan["days"]][0] == "Gornji dio tijela A"
    item = plan["days"][0]["exercises"][0]
    assert (
        item["target_sets"] >= 3 and item["rep_min"] <= item["rep_max"] and item["rest_seconds"] > 0
    )
    assert item["exercise"]["name"] and item["exercise"]["instructions"]


def test_accept_and_new_version_keeps_history(client):  # FIT-06, FIT-03
    me = auth_headers(client)
    save_profile(client, me)
    v1 = client.post("/api/v1/training-plans", headers=me).json()
    accepted = client.post(f"/api/v1/training-plans/{v1['id']}/accept", headers=me).json()
    assert accepted["status"] == "active" and accepted["accepted_at"]

    # New goal, new proposal: the active plan stays until the draft is accepted.
    save_profile(client, me, training_goal="strength")
    v2 = client.post("/api/v1/training-plans", headers=me).json()
    current = client.get("/api/v1/training-plans/current", headers=me).json()
    assert current["active"]["id"] == v1["id"]
    assert current["draft"]["id"] == v2["id"]
    assert current["draft"]["goal_snapshot"]["training_goal"] == "strength"

    client.post(f"/api/v1/training-plans/{v2['id']}/accept", headers=me)
    history = client.get("/api/v1/training-plans", headers=me).json()
    assert [(p["version"], p["status"]) for p in history] == [(2, "active"), (1, "archived")]
    # The old version is still readable with its original goal.
    old = client.get(f"/api/v1/training-plans/{v1['id']}", headers=me).json()
    assert old["goal_snapshot"]["training_goal"] == "muscle"
    assert old["days"]


def test_a_second_draft_replaces_the_first(client):
    me = auth_headers(client)
    save_profile(client, me)
    first = client.post("/api/v1/training-plans", headers=me).json()
    second = client.post("/api/v1/training-plans", headers=me).json()
    current = client.get("/api/v1/training-plans/current", headers=me).json()
    assert current["active"] is None and current["draft"]["id"] == second["id"]
    statuses = {
        p["id"]: p["status"] for p in client.get("/api/v1/training-plans", headers=me).json()
    }
    assert statuses == {first["id"]: "archived", second["id"]: "draft"}


def test_plans_are_private(client):
    ana = auth_headers(client)
    save_profile(client, ana)
    plan = client.post("/api/v1/training-plans", headers=ana).json()
    marko = auth_headers(client, "marko@example.com")
    assert client.get(f"/api/v1/training-plans/{plan['id']}", headers=marko).status_code == 404
    assert (
        client.post(f"/api/v1/training-plans/{plan['id']}/accept", headers=marko).status_code == 404
    )


def test_exercise_catalog_is_available(client):
    me = auth_headers(client)
    exercises = client.get("/api/v1/exercises", headers=me).json()
    assert len(exercises) >= 45
    assert {"goblet-squat", "plank", "treadmill"} <= {e["slug"] for e in exercises}
