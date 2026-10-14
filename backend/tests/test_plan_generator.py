import itertools

import pytest

from app.services.exercise_catalog import CATALOG
from app.services.plan_generator import CatalogExercise, generate

CATALOG_ROWS = [
    CatalogExercise(
        id=row["slug"],
        slug=row["slug"],
        movement=row["movement"],
        equipment=row["equipment"],
        difficulty_level=row["difficulty_level"],
        is_compound=row["is_compound"],
        unit=row["unit"],
    )
    for row in CATALOG
]
BY_SLUG = {row["slug"]: row for row in CATALOG}


def profile(**overrides):
    return {
        "training_goal": "muscle",
        "experience_level": "intermediate",
        "days_per_week": 3,
        "session_minutes": 60,
        "equipment": "gym",
        **overrides,
    }


@pytest.mark.parametrize(
    "goal, experience, days, equipment",
    list(
        itertools.product(
            ["strength", "muscle", "endurance", "fat_loss", "general"],
            ["beginner", "intermediate", "advanced"],
            [2, 3, 4, 5, 6],
            ["gym", "dumbbells", "bodyweight"],
        )
    ),
)
def test_every_profile_gets_a_valid_plan(goal, experience, days, equipment):
    p = profile(
        training_goal=goal, experience_level=experience, days_per_week=days, equipment=equipment
    )
    plan = generate(p, CATALOG_ROWS)
    expected_days = min(days, 4) if experience == "beginner" else days
    assert len(plan.days) == expected_days
    for day in plan.days:
        slugs = [item.exercise.slug for item in day.exercises]
        assert 3 <= len(slugs) <= 6
        assert len(slugs) == len(set(slugs)), "no exercise twice in one day"
        for item in day.exercises:
            assert 1 <= item.sets <= 5 and 1 <= item.rep_min <= item.rep_max
            assert (
                item.exercise.difficulty_level
                <= {"beginner": 1, "intermediate": 2, "advanced": 3}[experience]
            )
            if equipment == "bodyweight":
                assert item.exercise.equipment == "bodyweight"


def test_same_input_gives_same_plan_and_new_version_varies():
    first = generate(profile(), CATALOG_ROWS, version=1)
    again = generate(profile(), CATALOG_ROWS, version=1)
    second = generate(profile(), CATALOG_ROWS, version=2)
    names = lambda plan: [[i.exercise.slug for i in d.exercises] for d in plan.days]  # noqa: E731
    assert names(first) == names(again)
    assert names(first) != names(second)


def test_beginner_is_capped_and_told_why():
    plan = generate(profile(experience_level="beginner", days_per_week=6), CATALOG_ROWS)
    assert len(plan.days) == 4
    assert any("početnike" in note for note in plan.notes)
    first = plan.days[0].exercises[0]
    assert first.sets == 3  # one set fewer than the intermediate scheme


def test_strength_uses_heavy_low_reps_for_compounds():
    plan = generate(profile(training_goal="strength", session_minutes=90), CATALOG_ROWS)
    compound = next(i for i in plan.days[0].exercises if i.exercise.is_compound)
    assert (compound.sets, compound.rep_min, compound.rep_max, compound.rest_seconds) == (
        5,
        3,
        6,
        180,
    )


def test_fat_loss_days_end_with_cardio():
    plan = generate(profile(training_goal="fat_loss", session_minutes=45), CATALOG_ROWS)
    for day in plan.days:
        assert len(day.exercises) == 5
        last = day.exercises[-1]
        assert last.exercise.unit == "minutes" and last.sets == 1


def test_session_length_sets_exercise_count():
    short = generate(profile(session_minutes=30), CATALOG_ROWS)
    long = generate(profile(session_minutes=90), CATALOG_ROWS)
    assert all(len(d.exercises) == 4 for d in short.days)
    assert all(len(d.exercises) > 4 for d in long.days)
