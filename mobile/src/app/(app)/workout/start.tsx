import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { Banner, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

/** Pick a day from the active plan (sets come pre-filled) or start a free workout (LOG-01). */
export default function StartWorkoutScreen() {
  const { data, error } = useFocusData(async () => {
    const open = await api.currentWorkout();
    if (open) {
      router.replace(`/workout/${open.id}`);
      return null;
    }
    return (await api.currentPlans()).active;
  });
  const [starting, setStarting] = useState<string | null>(null);
  const [startError, setStartError] = useState<string | null>(null);

  async function start(planDayId: string | null) {
    if (starting) return;
    setStarting(planDayId ?? "free");
    setStartError(null);
    try {
      const workout = await api.startWorkout(planDayId);
      router.replace(`/workout/${workout.id}`);
    } catch (err) {
      setStartError(errorMessage(err));
      setStarting(null);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>{t.chooseWorkout}</Text>
      <Banner message={error ?? startError} />
      {data ? (
        <>
          <Muted>{t.chooseWorkoutHint}</Muted>
          {data.days.map((day) => (
            <Card key={day.id} onPress={() => start(day.id)}>
              <Text style={styles.dayLabel}>{t.dayN(day.day_number)}</Text>
              <Text style={styles.name}>{day.name}</Text>
              <Muted>
                {starting === day.id ? "…" : `${t.exercisesCount(day.exercises.length)}: `}
                {day.exercises.map((e) => e.exercise.name).join(", ")}
              </Muted>
            </Card>
          ))}
        </>
      ) : (
        !error && <Muted>{t.noActivePlan}</Muted>
      )}
      <SectionTitle>{t.freeWorkout}</SectionTitle>
      <Card onPress={() => start(null)}>
        <Text style={styles.name}>{starting === "free" ? "…" : t.freeWorkout}</Text>
        <Muted>{t.freeWorkoutHint}</Muted>
      </Card>
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 22, fontWeight: "800", color: colors.text },
  dayLabel: { fontSize: 12, fontWeight: "700", color: colors.primary, textTransform: "uppercase" },
  name: { fontSize: 17, fontWeight: "700", color: colors.text },
});
