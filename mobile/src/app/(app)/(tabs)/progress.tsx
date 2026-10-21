import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { BarChart } from "@/components/BarChart";
import { Banner, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { formatKg, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

/** Progress overview (LOG-05, LOG-06): weekly volume, new records and every exercise trained. */
export default function ProgressScreen() {
  const { data, error } = useFocusData(() => api.progressOverview());

  if (!data) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }
  if (data.total_workouts === 0) {
    return (
      <Screen>
        <Card>
          <Text style={styles.big}>📈</Text>
          <Muted>{t.progressEmpty}</Muted>
        </Card>
      </Screen>
    );
  }

  const thisWeek = data.weeks[data.weeks.length - 1];
  return (
    <Screen>
      <Banner message={error} />
      <View style={styles.stats}>
        <Stat value={String(data.total_workouts)} label={t.totalWorkouts} />
        <Stat value={String(thisWeek.workouts)} label={`${t.statWorkouts} ${t.thisWeek.toLowerCase()}`} />
        <Stat value={formatKg(thisWeek.volume_kg)} label={`kg ${t.thisWeek.toLowerCase()}`} />
      </View>

      <SectionTitle>{t.weeklyVolume}</SectionTitle>
      <Card>
        <BarChart
          bars={data.weeks.map((w) => ({
            key: w.week_start,
            value: w.volume_kg,
            label: t.shortDate(w.week_start),
            detail: `${t.shortDate(w.week_start)} · ${formatKg(w.volume_kg)} kg · ${w.workouts} ${t.statWorkouts}`,
            highlight: true,
          }))}
          format={(v) => `${formatKg(v)} kg`}
        />
        <Muted>{t.weeklyVolumeHint}</Muted>
      </Card>

      {data.recent_records.length > 0 && (
        <>
          <SectionTitle>{t.recentRecords}</SectionTitle>
          {data.recent_records.map((r) => (
            <Card key={`${r.exercise.id}-${r.date}`} onPress={() => router.push(`/progress/${r.exercise.id}`)}>
              <View style={styles.row}>
                <Text style={styles.name}>🏆 {r.exercise.name}</Text>
                <Text style={styles.value}>{t.topSet(r.weight_kg, r.reps, r.exercise.unit)}</Text>
              </View>
              <Muted>{t.date(r.date)}</Muted>
            </Card>
          ))}
        </>
      )}

      <SectionTitle>{t.yourExercises}</SectionTitle>
      {data.exercises.map((e) => (
        <Card key={e.exercise.id} onPress={() => router.push(`/progress/${e.exercise.id}`)}>
          <View style={styles.row}>
            <Text style={styles.name}>{e.exercise.name}</Text>
            <Text style={styles.chevron}>›</Text>
          </View>
          <Muted>
            {t.personalRecord}: {t.topSet(e.record.weight_kg, e.record.reps, e.exercise.unit)}
          </Muted>
          <Muted>
            {t.lastResult}: {t.topSet(e.last.weight_kg, e.last.reps, e.exercise.unit)} · {t.date(e.last.date)} ·{" "}
            {t.sessionsCount(e.sessions)}
          </Muted>
        </Card>
      ))}
    </Screen>
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
  big: { fontSize: 32 },
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
  statLabel: { fontSize: 12, color: colors.muted, marginTop: 2, textAlign: "center" },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  name: { fontSize: 16, fontWeight: "700", color: colors.text, flex: 1 },
  value: { fontSize: 15, fontWeight: "700", color: colors.primary },
  chevron: { fontSize: 22, color: colors.muted },
});
