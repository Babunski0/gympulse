from datetime import timedelta

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models import WorkoutSession
from app.models._base import utcnow
from tests.conftest import GYM, auth_headers
from tests.test_attendance import check_in, gym_with_member
from tests.test_training import save_profile

API = "/api/v1/workouts"


def exercise_id(client, headers, slug="bench-press"):
    exercises = client.get("/api/v1/exercises", headers=headers).json()
    return next(e["id"] for e in exercises if e["slug"] == slug)


def accepted_plan(client, headers):
    save_profile(client, headers)
    plan = client.post("/api/v1/training-plans", headers=headers).json()
    client.post(f"/api/v1/training-plans/{plan['id']}/accept", headers=headers)
    return plan


def free_workout(client, headers):
    res = client.post(API, json={}, headers=headers)
    assert res.status_code == 201
    return res.json()


def add_set(client, headers, workout_id, ex_id, reps=8, weight_kg=40, **extra):
    return client.post(
        f"{API}/{workout_id}/sets",
        json={"exercise_id": ex_id, "reps": reps, "weight_kg": weight_kg, **extra},
        headers=headers,
    )


def finish(client, headers, workout_id):
    return client.post(f"{API}/{workout_id}/finish", headers=headers)


def test_free_workout_logs_sets_and_counts_volume(client):  # LOG-01, LOG-02, TC-08
    me = auth_headers(client)
    workout = free_workout(client, me)
    assert (workout["plan_day_name"], workout["exercises"]) == (None, [])
    bench = exercise_id(client, me)
    for _ in range(3):
        res = add_set(client, me, workout["id"], bench, is_completed=True)
        assert res.status_code == 201
    add_set(
        client, me, workout["id"], bench, reps=12, weight_kg=20, is_completed=True, is_warmup=True
    )
    body = finish(client, me, workout["id"]).json()
    assert body["ended_at"] is not None
    assert body["total_volume_kg"] == 960  # 3 x 8 x 40; the warm-up does not count
    assert body["completed_sets"] == 4
    assert [s["set_number"] for s in body["exercises"][0]["sets"]] == [1, 2, 3, 4]


def test_negative_values_are_rejected(client):  # US-10
    me = auth_headers(client)
    workout = free_workout(client, me)
    bench = exercise_id(client, me)
    res = add_set(client, me, workout["id"], bench, reps=-1, weight_kg=-20)
    assert res.status_code == 422
    assert {d["field"] for d in res.json()["error"]["details"]} == {"reps", "weight_kg"}
    ok = add_set(client, me, workout["id"], bench).json()
    res = client.patch(f"{API}/{workout['id']}/sets/{ok['id']}", json={"weight_kg": -5}, headers=me)
    assert res.status_code == 422


def test_only_one_workout_at_a_time(client):
    me = auth_headers(client)
    free_workout(client, me)
    res = client.post(API, json={}, headers=me)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "workout_in_progress"


def test_plan_day_workout_is_prefilled_and_unfinished_sets_are_dropped(client):
    me = auth_headers(client)
    plan = accepted_plan(client, me)
    day = plan["days"][0]
    workout = client.post(API, json={"plan_day_id": day["id"]}, headers=me).json()
    assert workout["plan_day_name"] == day["name"]
    first = workout["exercises"][0]
    planned = day["exercises"][0]
    assert first["exercise"]["id"] == planned["exercise"]["id"]
    assert first["target"]["sets"] == len(first["sets"]) == planned["target_sets"]
    assert first["previous"] is None
    assert all(not s["is_completed"] for s in first["sets"])

    # Do two sets of the first exercise only.
    for s in first["sets"][:2]:
        client.patch(
            f"{API}/{workout['id']}/sets/{s['id']}",
            json={"reps": 10, "weight_kg": 50, "is_completed": True},
            headers=me,
        )
    done = finish(client, me, workout["id"]).json()
    assert [len(e["sets"]) for e in done["exercises"]] == [2]
    assert done["total_volume_kg"] == 1000

    # Next time, the same day starts from last time's numbers.
    again = client.post(API, json={"plan_day_id": day["id"]}, headers=me).json()
    first = again["exercises"][0]
    assert first["previous"]["weight_kg"] == 50
    assert (first["sets"][0]["reps"], first["sets"][0]["weight_kg"]) == (10, 50)


def test_finished_workout_can_be_corrected(client):  # LOG-03
    me = auth_headers(client)
    workout = free_workout(client, me)
    bench = exercise_id(client, me)
    s = add_set(client, me, workout["id"], bench, is_completed=True).json()
    finish(client, me, workout["id"])
    res = client.patch(f"{API}/{workout['id']}/sets/{s['id']}", json={"weight_kg": 45}, headers=me)
    assert res.status_code == 200
    history = client.get(API, headers=me).json()
    assert history[0]["total_volume_kg"] == 360
    extra = add_set(client, me, workout["id"], bench, is_completed=True).json()
    client.delete(f"{API}/{workout['id']}/sets/{extra['id']}", headers=me)
    assert client.get(f"{API}/{workout['id']}", headers=me).json()["completed_sets"] == 1


def test_history_lists_finished_workouts_newest_first(client):  # LOG-04
    me = auth_headers(client)
    bench = exercise_id(client, me)
    ids = []
    for weight in (40, 42.5):
        w = free_workout(client, me)
        add_set(client, me, w["id"], bench, weight_kg=weight, is_completed=True)
        finish(client, me, w["id"])
        ids.append(w["id"])
    open_one = free_workout(client, me)
    history = client.get(API, headers=me).json()
    assert [w["id"] for w in history] == ids[::-1]
    assert open_one["id"] not in [w["id"] for w in history]
    assert history[0]["exercise_count"] == 1
    detail = client.get(f"{API}/{open_one['id']}", headers=me).json()
    assert detail["exercises"] == []
    # "Last time" is the most recent finished workout.
    add_set(client, me, open_one["id"], bench)
    current = client.get(f"{API}/current", headers=me).json()["workout"]
    assert current["exercises"][0]["previous"]["weight_kg"] == 42.5


def test_workout_is_linked_to_the_gym_when_checked_in(client):
    _, gym_id, member = gym_with_member(client)
    check_in(client, member, gym_id)
    assert free_workout(client, member)["gym_name"] == GYM["name"]


def test_duration_and_delete(client):
    me = auth_headers(client)
    workout = free_workout(client, me)
    with SessionLocal() as db:
        db.execute(
            update(WorkoutSession)
            .where(WorkoutSession.id == workout["id"])
            .values(started_at=utcnow().replace(microsecond=0) - timedelta(minutes=47))
        )
        db.commit()
    assert finish(client, me, workout["id"]).json()["duration_minutes"] == 47
    assert client.delete(f"{API}/{workout['id']}", headers=me).status_code == 204
    assert client.get(API, headers=me).json() == []
    assert client.get(f"{API}/current", headers=me).json()["workout"] is None


def test_workouts_are_private(client):
    ana = auth_headers(client)
    workout = free_workout(client, ana)
    s = add_set(client, ana, workout["id"], exercise_id(client, ana)).json()
    marko = auth_headers(client, "marko@example.com")
    assert client.get(f"{API}/{workout['id']}", headers=marko).status_code == 404
    res = client.patch(f"{API}/{workout['id']}/sets/{s['id']}", json={"reps": 1}, headers=marko)
    assert res.status_code == 404
    assert client.delete(f"{API}/{workout['id']}", headers=marko).status_code == 404
    other_plan = accepted_plan(client, marko)
    res = client.post(API, json={"plan_day_id": other_plan["days"][0]["id"]}, headers=ana)
    assert res.status_code == 404
