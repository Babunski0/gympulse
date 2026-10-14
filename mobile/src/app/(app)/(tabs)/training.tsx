import { router } from "expo-router";
import { StyleSheet, Text } from "react-native";

import { Banner, Button, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

/** Everything about training in one tab: today's workout, the plan and recent workouts. */
export default function TrainingScreen() {
  const { data, error } = useFocusData(async () => {
    const [workout, plans, recent] = await Promise.all([
      api.currentWorkout(),
      api.currentPlans(),
      api.workoutHistory(5),
    ]);
    return { workout, plan: plans.active, recent };
  });

  return (
    <Screen>
      <Banner message={error} />
      {data?.workout ? (
        <Card onPress={() => router.push(`/workout/${data.workout!.id}`)}>
          <Text style={styles.title}>🔥 {t.workoutInProgress}</Text>
          <Muted>{data.workout.plan_day_name ?? t.freeWorkout}</Muted>
          <Text style={styles.link}>{t.continueWorkout} →</Text>
        </Card>
      ) : (
        data && <Button title={`🏋️  ${t.startWorkout}`} onPress={() => router.push("/workout/start")} />
      )}

      <SectionTitle>{t.myPlan}</SectionTitle>
      {data && (
        <Card onPress={() => router.push("/plan")}>
          {data.plan ? (
            <>
              <Text style={styles.title}>{data.plan.days.map((d) => d.name).join(" · ")}</Text>
              <Muted>{t.planCardHint}</Muted>
              <Text style={styles.link}>{t.myPlan} →</Text>
            </>
          ) : (
            <>
              <Text style={styles.title}>{t.noPlanYet}</Text>
              <Text style={styles.link}>{t.makePlan} →</Text>
            </>
          )}
        </Card>
      )}

      <SectionTitle>{t.recentWorkouts}</SectionTitle>
      {data?.recent.length === 0 && <Muted>{t.noWorkouts}</Muted>}
      {data?.recent.map((w) => (
        <Card key={w.id} onPress={() => router.push(`/workout/${w.id}`)}>
          <Text style={styles.date}>
            {t.date(w.started_at)} · {t.clock(w.started_at)}
          </Text>
          <Text style={styles.title}>{w.plan_day_name ?? t.freeWorkout}</Text>
          <Muted>{t.workoutStats(w.completed_sets, w.total_volume_kg, t.duration(w.duration_minutes))}</Muted>
        </Card>
      ))}
      {data && data.recent.length > 0 && (
        <Button title={t.seeAll} variant="ghost" onPress={() => router.push("/workout/history")} />
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 16, fontWeight: "700", color: colors.text },
  date: { fontSize: 12, fontWeight: "700", color: colors.primary, textTransform: "uppercase" },
  link: { fontSize: 15, fontWeight: "600", color: colors.primary },
});
