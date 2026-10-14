"""Deterministic training plan generator (FIT-04, FIT-05).

Same profile + same catalog + same version number always gives the same plan. The version
number shifts which variant of each movement is picked, so asking for a new proposal gives
different exercises for the same movements instead of an identical copy.
"""

from dataclasses import dataclass, field

GENERATOR_VERSION = "1"

MAX_DIFFICULTY = {"beginner": 1, "intermediate": 2, "advanced": 3}
ALLOWED_EQUIPMENT = {
    "gym": {"barbell", "dumbbell", "machine", "cable", "bodyweight"},
    "dumbbells": {"dumbbell", "bodyweight"},
    "bodyweight": {"bodyweight"},
}
# Beginners start with stable, easy-to-learn equipment; experienced lifters with free weights.
EQUIPMENT_PREFERENCE = {
    "beginner": ["machine", "dumbbell", "cable", "bodyweight", "barbell"],
    "other": ["barbell", "cable", "dumbbell", "machine", "bodyweight"],
}
BEGINNER_MAX_DAYS = 4

# A slot is (movement, variant). Variant 1 means "pick a different exercise than variant 0",
# so two days that both squat do not repeat the same squat. Slots are in priority order and
# are cut from the end when the session is short.
FULL_A = [
    ("squat", 0),
    ("push_horizontal", 0),
    ("pull_horizontal", 0),
    ("hinge", 0),
    ("push_vertical", 0),
    ("core", 0),
    ("arm_flexion", 0),
    ("calves", 0),
]
FULL_B = [
    ("hinge", 1),
    ("push_vertical", 1),
    ("pull_vertical", 0),
    ("lunge", 0),
    ("push_horizontal", 1),
    ("core", 1),
    ("arm_extension", 0),
    ("shoulder_isolation", 0),
]
FULL_C = [
    ("squat", 1),
    ("pull_vertical", 1),
    ("push_horizontal", 2),
    ("lunge", 1),
    ("pull_horizontal", 1),
    ("core", 2),
    ("chest_isolation", 0),
    ("knee_flexion", 0),
]
UPPER_A = [
    ("push_horizontal", 0),
    ("pull_horizontal", 0),
    ("push_vertical", 0),
    ("pull_vertical", 0),
    ("shoulder_isolation", 0),
    ("arm_flexion", 0),
    ("arm_extension", 0),
    ("core", 0),
]
UPPER_B = [
    ("push_vertical", 1),
    ("pull_vertical", 1),
    ("push_horizontal", 1),
    ("pull_horizontal", 1),
    ("chest_isolation", 0),
    ("arm_extension", 1),
    ("arm_flexion", 1),
    ("core", 1),
]
LOWER_A = [
    ("squat", 0),
    ("hinge", 0),
    ("lunge", 0),
    ("knee_flexion", 0),
    ("calves", 0),
    ("core", 2),
    ("knee_extension", 0),
]
LOWER_B = [
    ("hinge", 1),
    ("squat", 1),
    ("lunge", 1),
    ("knee_extension", 0),
    ("calves", 1),
    ("core", 3),
    ("knee_flexion", 0),
]
PUSH = [
    ("push_horizontal", 0),
    ("push_vertical", 0),
    ("push_horizontal", 1),
    ("shoulder_isolation", 0),
    ("chest_isolation", 0),
    ("arm_extension", 0),
    ("core", 0),
]
PULL = [
    ("pull_vertical", 0),
    ("pull_horizontal", 0),
    ("pull_horizontal", 1),
    ("shoulder_isolation", 1),
    ("arm_flexion", 0),
    ("arm_flexion", 1),
    ("core", 1),
]
LEGS = [("squat", 0), ("hinge", 0), ("lunge", 0), ("knee_flexion", 0), ("knee_extension", 0),
        ("calves", 0), ("core", 2)]  # fmt: skip

# (day name, slots, extra variant shift) per number of training days
SPLITS = {
    2: [("Cijelo tijelo A", FULL_A, 0), ("Cijelo tijelo B", FULL_B, 0)],
    3: [("Cijelo tijelo A", FULL_A, 0), ("Cijelo tijelo B", FULL_B, 0),
        ("Cijelo tijelo C", FULL_C, 0)],
    4: [("Gornji dio tijela A", UPPER_A, 0), ("Donji dio tijela A", LOWER_A, 0),
        ("Gornji dio tijela B", UPPER_B, 0), ("Donji dio tijela B", LOWER_B, 0)],
    5: [("Gornji dio tijela", UPPER_A, 0), ("Donji dio tijela", LOWER_A, 0),
        ("Guranje: grudi, ramena, triceps", PUSH, 1), ("Vučenje: leđa, biceps", PULL, 1),
        ("Noge", LEGS, 1)],
    6: [("Guranje: grudi, ramena, triceps", PUSH, 0), ("Vučenje: leđa, biceps", PULL, 0),
        ("Noge", LEGS, 0), ("Guranje: grudi, ramena, triceps (2)", PUSH, 1),
        ("Vučenje: leđa, biceps (2)", PULL, 1), ("Noge (2)", LEGS, 1)],
}  # fmt: skip
# Without a full gym there are too few pull and isolation exercises for push/pull/legs days,
# so 5-6 days alternate upper, lower and full-body days instead.
LIMITED_SPLITS = {
    5: [("Gornji dio tijela A", UPPER_A, 0), ("Donji dio tijela A", LOWER_A, 0),
        ("Gornji dio tijela B", UPPER_B, 0), ("Donji dio tijela B", LOWER_B, 0),
        ("Cijelo tijelo", FULL_C, 0)],
    6: [("Gornji dio tijela A", UPPER_A, 0), ("Donji dio tijela A", LOWER_A, 0),
        ("Gornji dio tijela B", UPPER_B, 0), ("Donji dio tijela B", LOWER_B, 0),
        ("Cijelo tijelo A", FULL_A, 1), ("Cijelo tijelo B", FULL_B, 1)],
}  # fmt: skip


@dataclass(frozen=True)
class Scheme:
    sets: int
    rep_min: int
    rep_max: int
    rest_seconds: int


# Sets and reps by goal, for compound (multi-joint) and isolation exercises.
SCHEMES = {
    "strength": (Scheme(5, 3, 6, 180), Scheme(3, 8, 12, 90)),
    "muscle": (Scheme(4, 6, 10, 120), Scheme(3, 10, 15, 60)),
    "endurance": (Scheme(3, 12, 20, 45), Scheme(3, 15, 20, 45)),
    "fat_loss": (Scheme(3, 10, 15, 60), Scheme(3, 12, 15, 45)),
    "general": (Scheme(3, 8, 12, 90), Scheme(3, 10, 15, 60)),
}
CARDIO_GOALS = {"endurance", "fat_loss"}


@dataclass(frozen=True)
class CatalogExercise:
    id: object
    slug: str
    movement: str
    equipment: str
    difficulty_level: int
    is_compound: bool
    unit: str


@dataclass
class PlannedExercise:
    exercise: CatalogExercise
    sets: int
    rep_min: int
    rep_max: int
    rest_seconds: int


@dataclass
class PlannedDay:
    name: str
    exercises: list[PlannedExercise] = field(default_factory=list)


@dataclass
class GeneratedPlan:
    days: list[PlannedDay]
    notes: list[str]


class PlanGenerationError(Exception):
    pass


def exercises_per_session(minutes: int) -> int:
    if minutes < 40:
        return 4
    if minutes < 55:
        return 5
    if minutes < 70:
        return 6
    if minutes < 85:
        return 7
    return 8


def scheme_for(goal: str, experience: str, exercise: CatalogExercise) -> Scheme:
    if exercise.unit == "minutes":  # cardio: one continuous block
        return Scheme(1, 15, 25, 0) if goal in CARDIO_GOALS else Scheme(1, 10, 15, 0)
    base = SCHEMES[goal][0 if exercise.is_compound else 1]
    if exercise.unit == "seconds":  # holds such as the plank
        base = Scheme(base.sets, 20, 45, 60)
    if experience == "beginner":
        # Fewer sets and no very heavy triples while technique is new.
        return Scheme(max(2, base.sets - 1), max(base.rep_min, 5), base.rep_max, base.rest_seconds)
    return base


def generate(profile: dict, catalog: list[CatalogExercise], version: int = 1) -> GeneratedPlan:
    goal = profile["training_goal"]
    experience = profile["experience_level"]
    days = profile["days_per_week"]
    notes: list[str] = []

    if experience == "beginner" and days > BEGINNER_MAX_DAYS:
        notes.append(
            f"Za početnike plan ima najviše {BEGINNER_MAX_DAYS} treninga nedjeljno; "
            "ostali dani su za odmor i oporavak."
        )
        days = BEGINNER_MAX_DAYS

    allowed = ALLOWED_EQUIPMENT[profile["equipment"]]
    max_difficulty = MAX_DIFFICULTY[experience]
    preference = EQUIPMENT_PREFERENCE["beginner" if experience == "beginner" else "other"]

    def candidates(movement: str) -> list[CatalogExercise]:
        usable = [
            e
            for e in catalog
            if e.movement == movement
            and e.equipment in allowed
            and e.difficulty_level <= max_difficulty
        ]
        if experience == "beginner":
            key = lambda e: (e.difficulty_level, preference.index(e.equipment), e.slug)  # noqa: E731
        else:
            key = lambda e: (-e.difficulty_level, preference.index(e.equipment), e.slug)  # noqa: E731
        return sorted(usable, key=key)

    per_session = exercises_per_session(profile["session_minutes"])
    shift = version - 1
    planned_days: list[PlannedDay] = []
    skipped = False
    splits = SPLITS if profile["equipment"] == "gym" else {**SPLITS, **LIMITED_SPLITS}
    for name, template, day_shift in splits[days]:
        slots = list(template)
        if goal in CARDIO_GOALS:
            slots = slots[: per_session - 1] + [("cardio", 0)]
        day = PlannedDay(name=name)
        used: set[str] = set()
        for movement, variant in slots:
            if len(day.exercises) >= per_session:
                break
            options = [e for e in candidates(movement) if e.slug not in used]
            if not options:
                skipped = True  # e.g. no machine for knee extensions at home
                continue
            pick = options[(variant + day_shift + shift) % len(options)]
            used.add(pick.slug)
            s = scheme_for(goal, experience, pick)
            day.exercises.append(
                PlannedExercise(pick, s.sets, s.rep_min, s.rep_max, s.rest_seconds)
            )
        if not day.exercises:
            raise PlanGenerationError("No exercises match this profile.")
        planned_days.append(day)

    if skipped:
        notes.append("Plan koristi samo opremu koju imaš, pa su neke vježbe izostavljene.")
    return GeneratedPlan(days=planned_days, notes=notes)
