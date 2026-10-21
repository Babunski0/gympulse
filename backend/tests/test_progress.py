from datetime import timedelta

from sqlalchemy import update

from app.core.db import SessionLocal
from app.models import WorkoutSession
from app.models._base import utcnow
from tests.conftest import auth_headers
from tests.test_workouts import add_set, exercise_id, finish, free_workout


def log_workout(client, headers, sets, days_ago):
    """sets: list of (slug, reps, kg) or (slug, reps, kg, warmup)."""
    w = free_workout(client, headers)
    for slug, reps, kg, *warm in sets:
        add_set(
            client,
            headers,
            w["id"],
            exercise_id(client, headers, slug),
            reps=reps,
            weight_kg=kg,
            is_completed=True,
            is_warmup=bool(warm and warm[0]),
        )
    with SessionLocal() as db:
        db.execute(
            update(WorkoutSession)
            .where(WorkoutSession.id == w["id"])
            .values(started_at=utcnow() - timedelta(days=days_ago, hours=1))
        )
        db.commit()
    return finish(client, headers, w["id"]).json()


def progress(client, headers, slug):
    return client.get(
        "/api/v1/progress",
        params={"exercise_id": exercise_id(client, headers, slug)},
        headers=headers,
    ).json()


def test_empty_state_is_not_an_invented_trend(client):  # US-11
    me = auth_headers(client)
    body = progress(client, me, "bench-press")
    assert (body["points"], body["record"], body["uses_weight"]) == ([], None, True)
    overview = client.get("/api/v1/progress/overview", headers=me).json()
    assert overview["exercises"] == [] and overview["total_workouts"] == 0
    assert len(overview["weeks"]) == 8 and all(w["volume_kg"] == 0 for w in overview["weeks"])


def test_history_by_date_with_top_set_volume_and_records(client):  # LOG-05, LOG-06
    me = auth_headers(client)
    log_workout(
        client,
        me,
        [("bench-press", 8, 50), ("bench-press", 8, 50), ("bench-press", 12, 20, True)],
        20,
    )
    log_workout(client, me, [("bench-press", 6, 55), ("bench-press", 5, 55)], 13)
    log_workout(client, me, [("bench-press", 10, 50)], 6)  # lighter: not a record
    log_workout(client, me, [("bench-press", 7, 55)], 1)  # same weight, more reps: a record
    body = progress(client, me, "bench-press")
    points = body["points"]
    assert [(p["weight_kg"], p["reps"]) for p in points] == [(50, 8), (55, 6), (50, 10), (55, 7)]
    assert [p["is_record"] for p in points] == [False, True, False, True]
    assert points[0]["sets"] == 2 and points[0]["volume_kg"] == 800  # warm-up left out
    assert points == sorted(points, key=lambda p: p["date"])
    assert (body["record"]["weight_kg"], body["record"]["reps"]) == (55, 7)


def test_bodyweight_records_count_reps(client):
    me = auth_headers(client)
    log_workout(client, me, [("push-up", 12, 0)], 3)
    log_workout(client, me, [("push-up", 15, 0)], 1)
    body = progress(client, me, "push-up")
    assert body["uses_weight"] is False
    assert [(p["weight_kg"], p["reps"], p["is_record"]) for p in body["points"]] == [
        (None, 12, False),
        (None, 15, True),
    ]


def test_overview_lists_exercises_weeks_and_recent_records(client):
    me = auth_headers(client)
    log_workout(client, me, [("bench-press", 8, 50), ("push-up", 10, 0)], 10)
    log_workout(client, me, [("bench-press", 8, 52.5)], 0)
    o = client.get("/api/v1/progress/overview", headers=me).json()
    assert o["total_workouts"] == 2
    assert [e["exercise"]["slug"] for e in o["exercises"]] == ["bench-press", "push-up"]
    bench = o["exercises"][0]
    assert (bench["sessions"], bench["record"]["weight_kg"], bench["last"]["weight_kg"]) == (
        2,
        52.5,
        52.5,
    )
    assert [r["exercise"]["slug"] for r in o["recent_records"]] == ["bench-press"]
    assert o["weeks"][-1]["volume_kg"] == 420  # 8 x 52.5 this week
    assert sum(w["workouts"] for w in o["weeks"]) == 2


def test_workout_marks_a_new_record(client):
    me = auth_headers(client)
    log_workout(client, me, [("bench-press", 8, 50)], 2)
    w = free_workout(client, me)
    add_set(
        client,
        me,
        w["id"],
        exercise_id(client, me, "bench-press"),
        reps=8,
        weight_kg=52.5,
        is_completed=True,
    )
    done = finish(client, me, w["id"]).json()
    group = done["exercises"][0]
    assert group["is_new_record"] is True and done["new_records"] == 1
    assert group["previous_record"]["weight_kg"] == 50


def test_progress_is_private(client):
    ana = auth_headers(client)
    log_workout(client, ana, [("bench-press", 8, 50)], 1)
    marko = auth_headers(client, "marko@example.com")
    assert progress(client, marko, "bench-press")["points"] == []
    res = client.get(
        "/api/v1/progress",
        params={"exercise_id": "00000000-0000-0000-0000-000000000000"},
        headers=marko,
    )
    assert res.status_code == 404
