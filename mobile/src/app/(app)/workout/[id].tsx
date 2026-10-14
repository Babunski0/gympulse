import { router, Stack, useLocalSearchParams } from "expo-router";
import { useEffect, useMemo, useState } from "react";
import { Pressable, StyleSheet, Text, TextInput, View } from "react-native";

import { Banner, Button, Card, Chip, ConfirmButton, Field, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, formatKg, t } from "@/i18n/sr";
import { api, type Exercise, type SetChanges, type Workout, type WorkoutExercise, type WorkoutSet } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

const DEFAULT_REST_SECONDS = 90;

/**
 * The workout logger (LOG-01..03). While the workout is open, each set is saved as soon as it is
 * ticked or edited; after it is finished, the same screen lets the user correct any set.
 */
export default function WorkoutScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: workout, error, setData, reload } = useFocusData(() => api.getWorkout(id), [id]);
  const [actionError, setActionError] = useState<string | null>(null);
  const [done, setDone] = useState<string | null>(null);
  const [picking, setPicking] = useState(false);
  const [busy, setBusy] = useState(false);
  const [rest, setRest] = useState<number | null>(null);

  useEffect(() => {
    if (rest === null) return;
    if (rest <= 0) {
      setRest(null);
      return;
    }
    const timer = setTimeout(() => setRest(rest - 1), 1000);
    return () => clearTimeout(timer);
  }, [rest]);

  const totals = useMemo(() => {
    const sets = workout?.exercises.flatMap((e) => e.sets) ?? [];
    const completed = sets.filter((s) => s.is_completed);
    const volume = completed.filter((s) => !s.is_warmup).reduce((sum, s) => sum + s.reps * s.weight_kg, 0);
    return { completed: completed.length, volume };
  }, [workout]);

  if (!workout) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }
  const finished = workout.ended_at !== null;

  function replaceSet(updated: WorkoutSet) {
    setData((w) =>
      w && {
        ...w,
        exercises: w.exercises.map((e) => ({
          ...e,
          sets: e.sets.map((s) => (s.id === updated.id ? updated : s)),
        })),
      },
    );
  }

  async function changeSet(group: WorkoutExercise, s: WorkoutSet, changes: SetChanges) {
    setActionError(null);
    replaceSet({ ...s, ...changes });
    if (changes.is_completed && !finished) setRest(group.target?.rest_seconds || DEFAULT_REST_SECONDS);
    try {
      replaceSet(await api.updateSet(workout!.id, s.id, changes));
    } catch (err) {
      setActionError(errorMessage(err));
      void reload();
    }
  }

  async function addSet(group: WorkoutExercise) {
    setActionError(null);
    const last = group.sets[group.sets.length - 1];
    const prev = group.previous;
    try {
      const created = await api.addSet(workout!.id, group.exercise.id, {
        reps: last?.reps ?? prev?.reps ?? 10,
        weight_kg: last?.weight_kg ?? prev?.weight_kg ?? 0,
        is_completed: finished, // a set added while correcting a finished workout was done
      });
      setData(
        (w) =>
          w && {
            ...w,
            exercises: w.exercises.map((e) =>
              e.exercise.id === group.exercise.id ? { ...e, sets: [...e.sets, created] } : e,
            ),
          },
      );
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  async function removeSet(s: WorkoutSet) {
    setActionError(null);
    setData(
      (w) =>
        w && {
          ...w,
          exercises: w.exercises.map((e) => ({ ...e, sets: e.sets.filter((x) => x.id !== s.id) })),
        },
    );
    try {
      await api.deleteSet(workout!.id, s.id);
    } catch (err) {
      setActionError(errorMessage(err));
      void reload();
    }
  }

  async function addExercise(exercise: Exercise) {
    setPicking(false);
    setActionError(null);
    try {
      const first = exercise.unit === "seconds" ? 30 : 10;
      await api.addSet(workout!.id, exercise.id, { reps: first, is_completed: finished });
      await reload(); // brings "last time" for the new exercise
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  async function finish() {
    setBusy(true);
    setActionError(null);
    try {
      const result = await api.finishWorkout(workout!.id);
      setData(result);
      setRest(null);
      setDone(t.workoutDone(formatKg(result.total_volume_kg), result.completed_sets));
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    try {
      await api.deleteWorkout(workout!.id);
      router.back();
    } catch (err) {
      setActionError(errorMessage(err));
      setBusy(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: workout.plan_day_name ?? t.freeWorkout }} />
      <Banner message={error ?? actionError} />
      <Banner message={done} tone="success" />
      <Card>
        <Text style={styles.headline}>
          {finished ? `${t.date(workout.started_at)} · ${t.clock(workout.started_at)}` : t.workoutInProgress}
        </Text>
        <Muted>
          {t.workoutStats(totals.completed, totals.volume, t.duration(workout.duration_minutes))}
          {workout.gym_name ? ` · ${workout.gym_name}` : ""}
        </Muted>
        {finished && <Muted>{t.editHint}</Muted>}
      </Card>
      {rest !== null && (
        <View style={styles.rest} accessibilityLiveRegion="polite">
          <Text style={styles.restText}>{t.restTimer(rest)}</Text>
          <Pressable accessibilityRole="button" onPress={() => setRest(null)}>
            <Text style={styles.restSkip}>{t.skipRest}</Text>
          </Pressable>
        </View>
      )}
      {workout.exercises.length === 0 && <Muted>{t.noSetsYet}</Muted>}
      {workout.exercises.map((group) => (
        <ExerciseCard
          key={group.exercise.id}
          group={group}
          onChange={(s, changes) => changeSet(group, s, changes)}
          onRemove={removeSet}
          onAddSet={() => addSet(group)}
        />
      ))}
      {picking ? (
        <ExercisePicker onPick={addExercise} onClose={() => setPicking(false)} />
      ) : (
        <Button title={t.addExercise} variant="ghost" onPress={() => setPicking(true)} />
      )}
      {!finished && <FinishButton onConfirm={finish} loading={busy} />}
      {finished && (
        <ConfirmButton
          title={t.deleteWorkout}
          question={t.deleteWorkoutQuestion}
          confirmTitle={t.deleteConfirm}
          cancelTitle={t.cancel}
          onConfirm={remove}
          loading={busy}
        />
      )}
    </Screen>
  );
}

function ExerciseCard(props: {
  group: WorkoutExercise;
  onChange: (s: WorkoutSet, changes: SetChanges) => void;
  onRemove: (s: WorkoutSet) => void;
  onAddSet: () => void;
}) {
  const { exercise, target, previous, sets } = props.group;
  const [showHow, setShowHow] = useState(false);
  return (
    <Card>
      <Pressable accessibilityRole="button" onPress={() => setShowHow(!showHow)}>
        <Text style={styles.exercise}>{exercise.name}</Text>
      </Pressable>
      {showHow && <Text style={styles.instructions}>{exercise.instructions}</Text>}
      {target && <Muted>{t.target(target.sets, target.rep_min, target.rep_max, exercise.unit)}</Muted>}
      {previous && <Muted>{t.lastTime(previous.reps, previous.weight_kg)}</Muted>}
      <View style={styles.headerRow}>
        <Text style={[styles.colHead, styles.colSet]}>{t.setLabel}</Text>
        <Text style={[styles.colHead, styles.colInput]}>{t.kg}</Text>
        <Text style={[styles.colHead, styles.colInput]}>{t.repsFor(exercise.unit)}</Text>
        <View style={styles.colTick} />
        <View style={styles.colRemove} />
      </View>
      {sets.map((s, i) => (
        <SetRow
          key={s.id}
          index={i + 1}
          set={s}
          onChange={(changes) => props.onChange(s, changes)}
          onRemove={() => props.onRemove(s)}
        />
      ))}
      <Button title={t.addSet} variant="ghost" onPress={props.onAddSet} />
    </Card>
  );
}

/** Accepts "42,5" as well as "42.5"; anything negative or not a number is rejected (US-10). */
function parseNumber(text: string): number | null {
  const clean = text.trim().replace(",", ".");
  if (!/^\d+(\.\d+)?$/.test(clean)) return null;
  const value = Number(clean);
  return value <= 1000 ? value : null;
}

function SetRow(props: {
  index: number;
  set: WorkoutSet;
  onChange: (changes: SetChanges) => void;
  onRemove: () => void;
}) {
  const s = props.set;
  const [kg, setKg] = useState(formatKg(s.weight_kg));
  const [reps, setReps] = useState(String(s.reps));
  const [invalid, setInvalid] = useState(false);

  useEffect(() => {
    setKg(formatKg(s.weight_kg));
    setReps(String(s.reps));
  }, [s.weight_kg, s.reps]);

  function read(): { weight_kg: number; reps: number } | null {
    const weight = parseNumber(kg);
    const count = parseNumber(reps);
    const ok = weight !== null && count !== null && Number.isInteger(count);
    setInvalid(!ok);
    return ok ? { weight_kg: weight, reps: count } : null;
  }

  function save() {
    const values = read();
    if (values && (values.weight_kg !== s.weight_kg || values.reps !== s.reps)) props.onChange(values);
  }

  function toggleDone() {
    const values = read();
    if (values) props.onChange({ ...values, is_completed: !s.is_completed });
  }

  return (
    <View>
      <View style={[styles.setRow, s.is_completed && styles.setRowDone]}>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={`${t.setLabel} ${props.index}${s.is_warmup ? `, ${t.warmup}` : ""}`}
          onPress={() => props.onChange({ is_warmup: !s.is_warmup })}
          style={styles.colSet}
        >
          <Text style={[styles.setNumber, s.is_warmup && styles.warmup]}>{s.is_warmup ? t.warmup : props.index}</Text>
        </Pressable>
        <TextInput
          style={[styles.input, styles.colInput, invalid && styles.inputError]}
          value={kg}
          onChangeText={setKg}
          onBlur={save}
          keyboardType="decimal-pad"
          selectTextOnFocus
          accessibilityLabel={`${t.setLabel} ${props.index} ${t.kg}`}
        />
        <TextInput
          style={[styles.input, styles.colInput, invalid && styles.inputError]}
          value={reps}
          onChangeText={setReps}
          onBlur={save}
          keyboardType="number-pad"
          selectTextOnFocus
          accessibilityLabel={`${t.setLabel} ${props.index} ${t.reps}`}
        />
        <Pressable
          accessibilityRole="checkbox"
          accessibilityState={{ checked: s.is_completed }}
          accessibilityLabel={t.markDone(props.index)}
          onPress={toggleDone}
          style={[styles.tick, s.is_completed && styles.tickDone, styles.colTick]}
        >
          <Text style={[styles.tickText, s.is_completed && styles.tickTextDone]}>✓</Text>
        </Pressable>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={t.removeSet(props.index)}
          onPress={props.onRemove}
          style={styles.colRemove}
        >
          <Text style={styles.remove}>×</Text>
        </Pressable>
      </View>
      {invalid && <Text style={styles.error}>{t.setInvalid}</Text>}
    </View>
  );
}

function ExercisePicker({ onPick, onClose }: { onPick: (e: Exercise) => void; onClose: () => void }) {
  const { data, error } = useFocusData(() => api.listExercises());
  const [query, setQuery] = useState("");
  const [group, setGroup] = useState<string | null>(null);
  const groups = useMemo(() => [...new Set((data ?? []).map((e) => e.muscle_group))], [data]);
  const q = query.trim().toLowerCase();
  const shown = (data ?? []).filter(
    (e) => (!group || e.muscle_group === group) && (!q || e.name.toLowerCase().includes(q)),
  );
  return (
    <Card>
      <Banner message={error} />
      <Field label={t.searchExercise} value={query} onChangeText={setQuery} autoFocus />
      <View style={styles.chips}>
        <Chip label={t.allGroups} selected={group === null} onPress={() => setGroup(null)} />
        {groups.map((g) => (
          <Chip key={g} label={t.muscleGroups[g] ?? g} selected={group === g} onPress={() => setGroup(g)} />
        ))}
      </View>
      {shown.map((e) => (
        <Pressable key={e.id} accessibilityRole="button" onPress={() => onPick(e)} style={styles.pickRow}>
          <Text style={styles.pickName}>{e.name}</Text>
          <Text style={styles.pickGroup}>{t.muscleGroups[e.muscle_group] ?? e.muscle_group}</Text>
        </Pressable>
      ))}
      <Button title={t.close} variant="ghost" onPress={onClose} />
    </Card>
  );
}

function FinishButton({ onConfirm, loading }: { onConfirm: () => void; loading: boolean }) {
  const [asking, setAsking] = useState(false);
  if (!asking) return <Button title={t.finishWorkout} onPress={() => setAsking(true)} />;
  return (
    <Card>
      <Text style={styles.question}>{t.finishQuestion}</Text>
      <Button title={t.finishConfirm} onPress={onConfirm} loading={loading} />
      <Button title={t.cancel} variant="ghost" onPress={() => setAsking(false)} />
    </Card>
  );
}

const styles = StyleSheet.create({
  headline: { fontSize: 18, fontWeight: "700", color: colors.text },
  exercise: { fontSize: 17, fontWeight: "700", color: colors.primary },
  instructions: { fontSize: 14, color: colors.text, lineHeight: 20 },
  headerRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, marginTop: spacing.sm },
  colHead: { fontSize: 12, fontWeight: "700", color: colors.muted, textAlign: "center" },
  colSet: { width: 44, alignItems: "center" },
  colInput: { flex: 1 },
  colTick: { width: 44 },
  colRemove: { width: 28, alignItems: "center" },
  setRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.xs,
    borderRadius: 8,
  },
  setRowDone: { backgroundColor: "#E8F5E9" },
  setNumber: { fontSize: 15, fontWeight: "700", color: colors.text },
  warmup: { fontSize: 12, color: colors.warning },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 8,
    paddingVertical: 8,
    fontSize: 16,
    textAlign: "center",
    color: colors.text,
    minWidth: 0,
  },
  inputError: { borderColor: colors.danger },
  tick: {
    height: 40,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: colors.border,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: colors.surface,
  },
  tickDone: { backgroundColor: colors.success, borderColor: colors.success },
  tickText: { fontSize: 18, color: colors.muted, fontWeight: "700" },
  tickTextDone: { color: "#FFFFFF" },
  remove: { fontSize: 22, color: colors.muted },
  error: { color: colors.danger, fontSize: 13, marginLeft: 52 },
  rest: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    padding: spacing.md,
    borderRadius: 12,
    backgroundColor: colors.primary,
  },
  restText: { color: colors.primaryText, fontSize: 18, fontWeight: "700" },
  restSkip: { color: colors.primaryText, fontSize: 15, textDecorationLine: "underline" },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  pickRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  pickName: { fontSize: 15, color: colors.text, flex: 1 },
  pickGroup: { fontSize: 13, color: colors.muted },
  question: { fontSize: 15, color: colors.text },
});
