import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { t } from "@/i18n/sr";
import type { Plan, PlanExercise } from "@/lib/api";

import { colors, spacing } from "./theme";
import { Card, Muted } from "./ui";

/** The days of a plan with each exercise's sets, reps and rest (FIT-05). */
export function PlanView({ plan }: { plan: Plan }) {
  const g = plan.goal_snapshot;
  return (
    <View style={{ gap: spacing.md }}>
      <Muted>{t.planFor(t.goals[g.training_goal], g.days_per_week, g.session_minutes)}</Muted>
      {plan.notes.map((note) => (
        <Muted key={note}>{note}</Muted>
      ))}
      {plan.days.map((day) => (
        <Card key={day.id}>
          <Text style={styles.dayLabel}>{t.dayN(day.day_number)}</Text>
          <Text style={styles.dayName}>{day.name}</Text>
          {day.exercises.map((item) => (
            <ExerciseRow key={item.id} item={item} />
          ))}
        </Card>
      ))}
    </View>
  );
}

function ExerciseRow({ item }: { item: PlanExercise }) {
  const [open, setOpen] = useState(false);
  const { exercise } = item;
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityLabel={`${exercise.name}, ${t.showHow}`}
      onPress={() => setOpen(!open)}
      style={styles.row}
    >
      <View style={styles.rowTop}>
        <Text style={styles.position}>{item.position}</Text>
        <View style={{ flex: 1, gap: 2 }}>
          <Text style={styles.name}>{exercise.name}</Text>
          <Text style={styles.scheme}>
            {t.setsReps(item.target_sets, item.rep_min, item.rep_max, exercise.unit)}
            {item.rest_seconds > 0 ? ` · ${t.rest(item.rest_seconds)}` : ""}
          </Text>
        </View>
        <Text style={styles.chevron}>{open ? "−" : "+"}</Text>
      </View>
      {open && <Text style={styles.instructions}>{exercise.instructions}</Text>}
    </Pressable>
  );
}

const styles = StyleSheet.create({
  dayLabel: { fontSize: 12, fontWeight: "700", color: colors.primary, textTransform: "uppercase" },
  dayName: { fontSize: 17, fontWeight: "700", color: colors.text, marginBottom: spacing.xs },
  row: { paddingVertical: spacing.sm, borderTopWidth: 1, borderTopColor: colors.border, gap: spacing.xs },
  rowTop: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  position: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: colors.background,
    textAlign: "center",
    lineHeight: 24,
    fontSize: 12,
    fontWeight: "700",
    color: colors.muted,
    overflow: "hidden",
  },
  name: { fontSize: 15, fontWeight: "600", color: colors.text },
  scheme: { fontSize: 14, color: colors.muted },
  chevron: { fontSize: 20, color: colors.primary, width: 20, textAlign: "center" },
  instructions: { fontSize: 14, color: colors.text, marginLeft: 32, lineHeight: 20 },
});
