import { router, Stack, useLocalSearchParams } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BarChart } from "@/components/BarChart";
import { Banner, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { formatKg, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

/** One exercise over time (US-11): best set per workout, volume, and the personal record. */
export default function ExerciseProgressScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data, error } = useFocusData(() => api.exerciseProgress(id), [id]);

  if (!data) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }
  const { exercise, points, record } = data;
  const unit = exercise.unit;
  const best = (p: { weight_kg: number | null; reps: number }) => t.topSet(p.weight_kg, p.reps, unit);

  return (
    <Screen>
      <Stack.Screen options={{ title: exercise.name }} />
      {points.length === 0 ? (
        <Muted>{t.exerciseEmpty}</Muted>
      ) : (
        <>
          {record && (
            <View style={styles.record}>
              <Text style={styles.recordLabel}>{t.personalRecord}</Text>
              <Text style={styles.recordValue}>{best(record)}</Text>
              <Text style={styles.recordDate}>{t.date(record.date)}</Text>
            </View>
          )}

          <SectionTitle>{t.bestSetChart(data.uses_weight)}</SectionTitle>
          <Card>
            <BarChart
              bars={points.map((p) => ({
                key: p.workout_id,
                value: data.uses_weight ? (p.weight_kg ?? 0) : p.reps,
                label: t.shortDate(p.date),
                detail: `${t.shortDate(p.date)} · ${best(p)}${p.is_record ? " 🏆" : ""}`,
                highlight: p.is_record,
              }))}
              format={(v) => (data.uses_weight ? `${formatKg(v)} kg` : String(v))}
            />
            <Muted>{t.recordLegend}</Muted>
          </Card>

          {data.uses_weight && (
            <>
              <SectionTitle>{t.volumeChart}</SectionTitle>
              <Card>
                <BarChart
                  bars={points.map((p) => ({
                    key: p.workout_id,
                    value: p.volume_kg,
                    label: t.shortDate(p.date),
                    detail: `${t.shortDate(p.date)} · ${formatKg(p.volume_kg)} kg`,
                    highlight: true,
                  }))}
                  height={100}
                  format={(v) => `${formatKg(v)} kg`}
                />
              </Card>
            </>
          )}

          <SectionTitle>{t.sessionsList}</SectionTitle>
          {[...points].reverse().map((p) => (
            <Card key={p.workout_id} onPress={() => router.push(`/workout/${p.workout_id}`)}>
              <View style={styles.row}>
                <Text style={styles.date}>{t.date(p.date)}</Text>
                <Text style={styles.value}>
                  {p.is_record ? "🏆 " : ""}
                  {best(p)}
                </Text>
              </View>
              <Muted>{t.sessionLine(p.sets, p.volume_kg, data.uses_weight)}</Muted>
            </Card>
          ))}
        </>
      )}
    </Screen>
  );
}

const styles = StyleSheet.create({
  record: { backgroundColor: colors.primary, borderRadius: 16, padding: spacing.lg - 4, gap: 2 },
  recordLabel: { color: "#D6E4FF", fontSize: 13, fontWeight: "700", textTransform: "uppercase" },
  recordValue: { color: colors.primaryText, fontSize: 28, fontWeight: "800" },
  recordDate: { color: "#E3ECFF", fontSize: 14 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center" },
  date: { fontSize: 15, fontWeight: "600", color: colors.text },
  value: { fontSize: 15, fontWeight: "700", color: colors.primary },
});
