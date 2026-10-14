"""Curated exercise catalog. The plan generator only ever picks from this list.

difficulty: 1 = fine for beginners, 2 = intermediate, 3 = advanced technique.
unit: what a plan's rep range counts (reps, seconds held, or minutes of cardio).
Rows are matched by slug, so editing a name or instruction here updates the database too.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Exercise


def _ex(slug, name, group, movement, equipment, difficulty, compound, instructions, unit="reps"):
    return {
        "slug": slug,
        "name": name,
        "muscle_group": group,
        "movement": movement,
        "equipment": equipment,
        "difficulty_level": difficulty,
        "is_compound": compound,
        "unit": unit,
        "instructions": instructions,
    }


CATALOG: list[dict] = [
    # Noge i zadnjica
    _ex("goblet-squat", "Goblet čučanj", "legs", "squat", "dumbbell", 1, True,
        "Drži bučicu uz grudi, spusti se između koljena, grudi gore, pa se odgurni petama."),
    _ex("back-squat", "Čučanj sa šipkom", "legs", "squat", "barbell", 2, True,
        "Šipka na gornjem dijelu leđa, zategni stomak, spusti se koliko kontrolišeš i ustani."),
    _ex("leg-press", "Potisak nogama (leg press)", "legs", "squat", "machine", 1, True,
        "Stopala u širini ramena, spuštaj do oko 90° u koljenima, ne zaključavaj koljena."),
    _ex("bodyweight-squat", "Čučanj bez opterećenja", "legs", "squat", "bodyweight", 1, True,
        "Ruke ispred sebe, sjedi unazad i dole, koljena prate pravac prstiju."),
    _ex("romanian-deadlift", "Rumunsko mrtvo dizanje sa šipkom", "hamstrings", "hinge",
        "barbell", 2, True,
        "Blago savijena koljena, kukove guraj unazad ravnih leđa dok ne osjetiš zadnju ložu."),
    _ex("dumbbell-rdl", "Rumunsko mrtvo dizanje sa bučicama", "hamstrings", "hinge",
        "dumbbell", 1, True, "Bučice blizu nogu, pregni se u kukovima, leđa ostaju prava."),
    _ex("deadlift", "Mrtvo dizanje", "back", "hinge", "barbell", 3, True,
        "Šipka iznad sredine stopala, zategni se, odgurni pod i završi stiskom zadnjice."),
    _ex("hip-thrust", "Hip thrust sa šipkom", "glutes", "hinge", "barbell", 2, True,
        "Leđa na klupi, šipka na kukovima, podigni kukove do ravne linije i stisni zadnjicu."),
    _ex("glute-bridge", "Glute most", "glutes", "hinge", "bodyweight", 1, True,
        "Lezi na leđa, stopala na podu, podigni kukove i stisni zadnjicu na vrhu."),
    _ex("walking-lunge", "Iskorak u hodu sa bučicama", "legs", "lunge", "dumbbell", 2, True,
        "Dug korak, zadnje koljeno ka podu, odgurni se petom prednje noge."),
    _ex("step-up", "Penjanje na klupu", "legs", "lunge", "dumbbell", 1, True,
        "Cijelo stopalo na klupi, popni se snagom prednje noge, spuštaj se polako."),
    _ex("split-squat", "Split čučanj", "legs", "lunge", "bodyweight", 1, True,
        "Jedna noga naprijed, druga nazad, spuštaj se pravo dole uspravnog trupa."),
    _ex("leg-curl", "Pregib nogu na mašini", "hamstrings", "knee_flexion", "machine", 1, False,
        "Povuci jastuk ka sebi kontrolisano, zadrži sekund, spuštaj polako."),
    _ex("leg-extension", "Opružanje nogu na mašini", "legs", "knee_extension", "machine", 1,
        False, "Opruži noge do kraja bez zamaha, pa ih polako vrati."),
    _ex("calf-raise", "Podizanje na prste na mašini", "calves", "calves", "machine", 1, False,
        "Pune istegnutosti dole, podigni se na prste i zadrži sekund gore."),
    _ex("bodyweight-calf-raise", "Podizanje na prste", "calves", "calves", "bodyweight", 1, False,
        "Stani na ivicu stepenika, spusti pete, pa se podigni na prste."),
    # Guranje: grudi, ramena, triceps
    _ex("bench-press", "Bench press sa šipkom", "chest", "push_horizontal", "barbell", 2, True,
        "Lopatke skupljene, spusti šipku do sredine grudi i potisni. Koristi čuvara."),
    _ex("dumbbell-bench-press", "Potisak bučicama na ravnoj klupi", "chest", "push_horizontal",
        "dumbbell", 1, True, "Spusti bučice pored grudi, potisni gore i blago ka sredini."),
    _ex("incline-dumbbell-press", "Potisak bučicama na kosoj klupi", "chest", "push_horizontal",
        "dumbbell", 2, True, "Klupa na oko 30°, spuštaj bučice ka gornjem dijelu grudi."),
    _ex("chest-press-machine", "Potisak na mašini za grudi", "chest", "push_horizontal",
        "machine", 1, True, "Ručke u visini grudi, potisni naprijed bez zaključavanja laktova."),
    _ex("push-up", "Sklekovi", "chest", "push_horizontal", "bodyweight", 1, True,
        "Tijelo u pravoj liniji, grudi skoro do poda, pa se odgurni. Lakše: koljena na podu."),
    _ex("overhead-press", "Potisak šipke iznad glave", "shoulders", "push_vertical", "barbell",
        2, True, "Zategni stomak i zadnjicu, potisni šipku iznad glave, glava prođe naprijed."),
    _ex("dumbbell-shoulder-press", "Potisak bučicama iznad glave", "shoulders", "push_vertical",
        "dumbbell", 1, True, "Sjedi oslonjen, potisni bučice gore, spusti ih do visine ušiju."),
    _ex("pike-push-up", "Pike sklekovi", "shoulders", "push_vertical", "bodyweight", 2, True,
        "Kukovi visoko kao obrnuto slovo V, spuštaj glavu ka podu između šaka."),
    _ex("lateral-raise", "Odručenje bučicama", "shoulders", "shoulder_isolation", "dumbbell", 1,
        False, "Laktovi blago savijeni, podigni bučice do visine ramena, spuštaj polako."),
    _ex("cable-fly", "Razvlačenje na sajli", "chest", "chest_isolation", "cable", 1, False,
        "Blago savijeni laktovi, spoji ruke ispred grudi u luku, vraćaj kontrolisano."),
    _ex("dumbbell-fly", "Razvlačenje bučicama", "chest", "chest_isolation", "dumbbell", 2, False,
        "Na klupi, ruke blago savijene, spuštaj bučice u stranu dok osjećaš istezanje."),
    _ex("triceps-pushdown", "Opružanje za triceps na sajli", "triceps", "arm_extension", "cable",
        1, False, "Laktovi uz tijelo, opruži ruke do kraja, vraćaj polako."),
    _ex("overhead-triceps-extension", "Francuski potisak bučicom", "triceps", "arm_extension",
        "dumbbell", 1, False, "Bučica iza glave objema rukama, opruži ruke gore, laktovi mirni."),
    _ex("bench-dip", "Propadanja na klupi", "triceps", "arm_extension", "bodyweight", 1, False,
        "Šake na ivici klupe, savij laktove unazad i spusti se, pa se odgurni."),
    # Vučenje: leđa, biceps
    _ex("lat-pulldown", "Lat povlačenje", "back", "pull_vertical", "cable", 1, True,
        "Povuci šipku do gornjeg dijela grudi, vodi laktovima, ne zabacuj se mnogo."),
    _ex("pull-up", "Zgibovi", "back", "pull_vertical", "bodyweight", 3, True,
        "Iz punog visa povuci bradu iznad šipke, spuštaj se kontrolisano."),
    _ex("barbell-row", "Veslanje sa šipkom u pretklonu", "back", "pull_horizontal", "barbell",
        2, True, "Pretklon oko 45°, povuci šipku ka donjim rebrima, leđa prava."),
    _ex("dumbbell-row", "Veslanje jednom bučicom", "back", "pull_horizontal", "dumbbell", 1,
        True, "Osloni se na klupu, povuci bučicu ka kuku, leđa ravna."),
    _ex("seated-cable-row", "Veslanje na sajli (sjedeći)", "back", "pull_horizontal", "cable", 1,
        True, "Sjedi uspravno, povuci ručku ka stomaku i skupi lopatke."),
    _ex("inverted-row", "Australijski zgibovi", "back", "pull_horizontal", "bodyweight", 2, True,
        "Ispod niske šipke ili čvrstog stola, tijelo pravo, povuci grudi do šipke."),
    _ex("door-row", "Veslanje uz dovratak", "back", "pull_horizontal", "bodyweight", 1, True,
        "Uhvati dovratak objema rukama, nagni se unazad pravog tijela i povuci se ka vratima."),
    _ex("dumbbell-pullover", "Pullover bučicom", "back", "pull_vertical", "dumbbell", 1, True,
        "Leđima na klupi, bučica iznad grudi, spuštaj je iza glave u luku, pa vrati."),
    _ex("face-pull", "Face pull na sajli", "shoulders", "shoulder_isolation", "cable", 1, False,
        "Uže u visini lica, povuci ka čelu i raširi ruke, laktovi visoko."),
    _ex("dumbbell-curl", "Pregib bučicama za biceps", "biceps", "arm_flexion", "dumbbell", 1,
        False, "Laktovi mirni uz tijelo, pregni ruke gore, spuštaj polako."),
    _ex("hammer-curl", "Čekić pregib", "biceps", "arm_flexion", "dumbbell", 1, False,
        "Dlanovi okrenuti jedan ka drugom, pregni ruke bez zamaha."),
    # Stomak
    _ex("plank", "Plank", "core", "core", "bodyweight", 1, False,
        "Podlaktice ispod ramena, tijelo pravo od glave do peta. Mjeri se u sekundama.", "seconds"),
    _ex("dead-bug", "Dead bug", "core", "core", "bodyweight", 1, False,
        "Na leđima, ruke i koljena gore, naizmjenično spuštaj suprotnu ruku i nogu."),
    _ex("hanging-knee-raise", "Podizanje koljena u visu", "core", "core", "bodyweight", 2, False,
        "Visi na šipki, podigni koljena ka grudima bez ljuljanja."),
    _ex("cable-crunch", "Trbušnjaci na sajli", "core", "core", "cable", 1, False,
        "Klečeći, savij rebra ka kukovima, kukovi ostaju mirni."),
    # Kondicija (mjeri se u minutama)
    _ex("treadmill", "Brzo hodanje ili trčanje na traci", "cardio", "cardio", "machine", 1, False,
        "Tempo pri kome možeš da govoriš u kratkim rečenicama.", "minutes"),
    _ex("stationary-bike", "Sobni bicikl", "cardio", "cardio", "machine", 1, False,
        "Ujednačen tempo, sjedište u visini kuka.", "minutes"),
    _ex("rowing-machine", "Veslanje na ergometru", "cardio", "cardio", "machine", 2, False,
        "Odgurni se nogama, pa povuci rukama; vraćaj se obrnutim redom.", "minutes"),
    _ex("brisk-walk", "Brzo hodanje napolju", "cardio", "cardio", "bodyweight", 1, False,
        "Hodaj brzo, tako da se zadihaš, ali da možeš da pričaš.", "minutes"),
    _ex("bodyweight-circuit", "Kružni trening: ski skokovi, čučnjevi, sklekovi", "cardio",
        "cardio", "bodyweight", 2, False,
        "Po 40 s svake vježbe bez pauze, pa minut odmora; ponavljaj do kraja vremena.",
        "minutes"),
]  # fmt: skip


def sync_catalog(db: Session) -> None:
    """Insert new catalog rows and update changed ones (matched by slug). Idempotent and cheap."""
    existing = {e.slug: e for e in db.scalars(select(Exercise))}
    changed = False
    for row in CATALOG:
        exercise = existing.get(row["slug"])
        if exercise is None:
            db.add(Exercise(**row))
            changed = True
            continue
        for field, value in row.items():
            if getattr(exercise, field) != value:
                setattr(exercise, field, value)
                changed = True
    if changed:
        db.commit()
