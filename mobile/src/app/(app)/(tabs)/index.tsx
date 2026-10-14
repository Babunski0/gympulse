import { router } from "expo-router";
import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { CurrentVisit } from "@/components/CurrentVisit";
import { Banner, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, formatKg, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function HomeScreen() {
  const { user } = useAuth();
  const firstName = user?.full_name.split(" ")[0] ?? "";
  // Refreshed every minute so the visit and workout lengths keep counting.
  const { data, error, setData, reload } = useFocusData(
    async () => {
      const [visit, workout, summary] = await Promise.all([
        api.currentAttendance(),
        api.currentWorkout(),
        api.homeSummary(),
      ]);
      return { visit, workout, summary };
    },
    [],
    60_000,
  );
  const [busy, setBusy] = useState<"checkout" | "start" | null>(null);
  const [notice, setNotice] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  async function checkOut() {
    setBusy("checkout");
    setActionError(null);
    try {
      const done = await api.checkOut();
      setData((d) => d && { ...d, visit: null });
      setNotice(t.checkedOut(t.duration(done.duration_minutes)));
    } catch (err) {
      setActionError(errorMessage(err));
      void reload();
    } finally {
      setBusy(null);
    }
  }

  async function startDay(planDayId: string) {
    setBusy("start");
    setActionError(null);
    try {
      const workout = await api.startWorkout(planDayId);
      router.push(`/workout/${workout.id}`);
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  const summary = data?.summary;
  const onboarding = summary && (!summary.has_profile || !summary.has_active_plan || summary.active_gyms === 0);

  return (
    <Screen>
      <Text style={styles.hello}>{t.hello(firstName)}</Text>
      <Banner message={error ?? actionError} />
      <Banner message={notice} tone="success" />

      {data?.workout ? (
        <Hero
          label={t.workoutInProgress}
          title={data.workout.plan_day_name ?? t.freeWorkout}
          detail={t.workoutStartedAt(t.clock(data.workout.started_at), t.duration(data.workout.duration_minutes))}
          action={`${t.continueShort} →`}
          onPress={() => router.push(`/workout/${data.workout!.id}`)}
        />
      ) : summary?.next_day ? (
        <Hero
          label={`${t.nextWorkout} · ${t.dayN(summary.next_day.day_number)}`}
          title={summary.next_day.name}
          detail={summary.next_day.exercise_names.join(" · ")}
          action={busy === "start" ? "…" : `${t.startThis} →`}
          onPress={() => startDay(summary.next_day!.id)}
          secondary={t.pickOther}
          onSecondary={() => router.push("/workout/start")}
        />
      ) : null}

      {data?.visit ? (
        <CurrentVisit session={data.visit} onCheckOut={checkOut} checkingOut={busy === "checkout"} />
      ) : (
        data && (
          <Card onPress={() => router.navigate("/gyms")}>
            <Text style={styles.cardTitle}>📍 {t.notInGym}</Text>
            <Text style={styles.link}>{t.goToGyms}</Text>
          </Card>
        )
      )}

      {onboarding && (
        <Card>
          <Text style={styles.cardTitle}>{t.firstSteps}</Text>
          <Muted>{t.firstStepsHint}</Muted>
          <Step done={summary.has_profile} label={t.stepProfile} onPress={() => router.push("/fitness")} />
          <Step done={summary.has_active_plan} label={t.stepPlan} onPress={() => router.push("/plan")} />
          <Step done={summary.active_gyms > 0} label={t.stepGym} onPress={() => router.navigate("/gyms")} />
        </Card>
      )}

      {summary && (
        <>
          <SectionTitle>{t.thisWeek}</SectionTitle>
          <View style={styles.stats}>
            <Stat value={String(summary.week.workouts)} label={t.statWorkouts} />
            <Stat value={String(summary.week.completed_sets)} label={t.statSets} />
            <Stat value={formatKg(summary.week.total_volume_kg)} label={t.statKg} />
          </View>
        </>
      )}

      {summary?.last_workout && (
        <>
          <SectionTitle>{t.lastWorkout}</SectionTitle>
          <Card onPress={() => router.push(`/workout/${summary.last_workout!.id}`)}>
            <Text style={styles.small}>{t.date(summary.last_workout.started_at)}</Text>
            <Text style={styles.cardTitle}>{summary.last_workout.plan_day_name ?? t.freeWorkout}</Text>
            <Muted>
              {t.workoutStats(
                summary.last_workout.completed_sets,
                summary.last_workout.total_volume_kg,
                t.duration(summary.last_workout.duration_minutes),
              )}
            </Muted>
          </Card>
        </>
      )}
    </Screen>
  );
}

function Hero(props: {
  label: string;
  title: string;
  detail: string;
  action: string;
  onPress: () => void;
  secondary?: string;
  onSecondary?: () => void;
}) {
  return (
    <View style={styles.hero}>
      <Text style={styles.heroLabel}>{props.label}</Text>
      <Text style={styles.heroTitle}>{props.title}</Text>
      <Text style={styles.heroDetail}>{props.detail}</Text>
      <Pressable accessibilityRole="button" onPress={props.onPress} style={styles.heroButton}>
        <Text style={styles.heroButtonText}>{props.action}</Text>
      </Pressable>
      {props.secondary && (
        <Pressable accessibilityRole="button" onPress={props.onSecondary}>
          <Text style={styles.heroSecondary}>{props.secondary}</Text>
        </Pressable>
      )}
    </View>
  );
}

function Step({ done, label, onPress }: { done: boolean; label: string; onPress: () => void }) {
  return (
    <Pressable accessibilityRole="button" onPress={onPress} disabled={done} style={styles.step}>
      <Text style={[styles.stepMark, done && styles.stepMarkDone]}>{done ? "✓" : ""}</Text>
      <Text style={[styles.stepLabel, done && styles.stepLabelDone]}>{label}</Text>
      {!done && <Text style={styles.link}>→</Text>}
    </Pressable>
  );
}

function Stat({ value, label }: { value: string; label: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statLabel}>{label}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  hello: { fontSize: 26, fontWeight: "800", color: colors.text },
  cardTitle: { fontSize: 16, fontWeight: "700", color: colors.text },
  small: { fontSize: 12, fontWeight: "700", color: colors.primary, textTransform: "uppercase" },
  link: { fontSize: 15, fontWeight: "600", color: colors.primary },
  hero: { backgroundColor: colors.primary, borderRadius: 16, padding: spacing.lg - 4, gap: spacing.xs },
  heroLabel: { color: "#D6E4FF", fontSize: 12, fontWeight: "700", textTransform: "uppercase" },
  heroTitle: { color: colors.primaryText, fontSize: 22, fontWeight: "800" },
  heroDetail: { color: "#E3ECFF", fontSize: 14, lineHeight: 20 },
  heroButton: {
    marginTop: spacing.sm,
    backgroundColor: colors.surface,
    borderRadius: 10,
    paddingVertical: 14,
    alignItems: "center",
  },
  heroButtonText: { color: colors.primary, fontSize: 16, fontWeight: "700" },
  heroSecondary: { color: colors.primaryText, fontSize: 14, textAlign: "center", marginTop: spacing.sm },
  step: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    paddingVertical: spacing.sm,
    borderTopWidth: 1,
    borderTopColor: colors.border,
  },
  stepMark: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: colors.border,
    textAlign: "center",
    lineHeight: 20,
    color: colors.primaryText,
    fontWeight: "700",
    overflow: "hidden",
  },
  stepMarkDone: { backgroundColor: colors.success, borderColor: colors.success },
  stepLabel: { flex: 1, fontSize: 15, color: colors.text },
  stepLabelDone: { color: colors.muted, textDecorationLine: "line-through" },
  stats: { flexDirection: "row", gap: spacing.sm },
  stat: {
    flex: 1,
    backgroundColor: colors.surface,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: colors.border,
    padding: spacing.md,
    alignItems: "center",
  },
  statValue: { fontSize: 22, fontWeight: "800", color: colors.text },
  statLabel: { fontSize: 12, color: colors.muted, marginTop: 2 },
});
