import { router } from "expo-router";
import { StyleSheet, Text } from "react-native";

import { Banner, Card, Muted, Screen } from "@/components/ui";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

/** Finished workouts, newest first (LOG-04). */
export default function WorkoutHistoryScreen() {
  const { data, error } = useFocusData(() => api.workoutHistory());
  return (
    <Screen>
      <Banner message={error} />
      {data?.length === 0 && <Muted>{t.noWorkouts}</Muted>}
      {data?.map((w) => (
        <Card key={w.id} onPress={() => router.push(`/workout/${w.id}`)}>
          <Text style={styles.date}>
            {t.date(w.started_at)} · {t.clock(w.started_at)}
          </Text>
          <Text style={styles.name}>{w.plan_day_name ?? t.freeWorkout}</Text>
          <Muted>{t.workoutStats(w.completed_sets, w.total_volume_kg, t.duration(w.duration_minutes))}</Muted>
          {w.gym_name && <Muted>{w.gym_name}</Muted>}
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  date: { fontSize: 12, fontWeight: "700", color: colors.primary, textTransform: "uppercase" },
  name: { fontSize: 17, fontWeight: "700", color: colors.text },
});
