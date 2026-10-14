from types import SimpleNamespace

import pytest

from app.services.recommendations import estimate, progress
from tests.conftest import auth_headers
from tests.test_training import save_profile


def ex(slug, movement="push_horizontal", equipment="barbell", unit="reps", compound=True):
    return SimpleNamespace(
        slug=slug, movement=movement, equipment=equipment, unit=unit, is_compound=compound
    )


def profile(weight=80.0, experience="intermediate", goal="muscle"):
    return SimpleNamespace(weight_kg=weight, experience_level=experience, training_goal=goal)


def done(*pairs):
    return [SimpleNamespace(weight_kg=w, reps=r) for w, r in pairs]


BENCH = ex("bench-press")
PUSH_UP = ex("push-up", equipment="bodyweight")
PLANK = ex("plank", movement="core", equipment="bodyweight", unit="seconds", compound=False)
CURL = ex("dumbbell-curl", movement="arm_flexion", equipment="dumbbell", compound=False)


def test_estimate_scales_with_body_weight_and_experience():
    light = estimate(BENCH, profile(60, "beginner"), 6, 10)
    heavy = estimate(BENCH, profile(100, "advanced"), 6, 10)
    assert light.weight_kg < heavy.weight_kg
    assert light.weight_kg % 2.5 == 0 and light.weight_kg >= 20  # at least the empty bar
    assert light.reps == 8 and light.basis == "estimate"


def test_dumbbells_are_per_hand_and_no_profile_weight_is_flagged():
    rec = estimate(CURL, profile(weight=None), 10, 15)
    assert rec.per_hand and rec.estimated_from_default_weight
    assert 2 <= rec.weight_kg <= 12


@pytest.mark.parametrize("exercise", [PUSH_UP, PLANK])
def test_bodyweight_and_timed_exercises_get_reps_only(exercise):
    rec = estimate(exercise, profile(), 8, 12)
    assert rec.weight_kg is None and rec.basis == "bodyweight"
    assert progress(exercise, done((0, 9), (0, 8)), 8, 12).weight_kg is None
    assert progress(exercise, done((0, 9), (0, 8)), 8, 12).reps == 10


def test_double_progression():
    assert progress(BENCH, done((60, 10), (60, 10), (60, 10)), 6, 10).weight_kg == 62.5
    same = progress(BENCH, done((60, 10), (60, 8), (60, 7)), 6, 10)
    assert (same.weight_kg, same.reps, same.basis) == (60, 10, "same")
    down = progress(BENCH, done((60, 3), (60, 2)), 6, 10)
    assert (down.weight_kg, down.basis) == (57.5, "decrease")
    squat = ex("back-squat", movement="squat")
    assert progress(squat, done((100, 8), (100, 8)), 5, 8).weight_kg == 105


def test_plan_shows_a_recommendation_for_every_exercise(client):
    me = auth_headers(client)
    save_profile(client, me, equipment="dumbbells")
    plan = client.post("/api/v1/training-plans", headers=me).json()
    for day in plan["days"]:
        for item in day["exercises"]:
            rec = item["recommendation"]
            bodyweight = item["exercise"]["equipment"] == "bodyweight"
            assert (rec["weight_kg"] is None) == (bodyweight or item["exercise"]["unit"] != "reps")
            assert item["rep_min"] <= rec["reps"] <= item["rep_max"]
