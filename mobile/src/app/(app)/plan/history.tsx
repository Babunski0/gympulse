import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { Badge, Banner, Card, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

const tone = { active: "success", draft: "warning", archived: "muted" } as const;

export default function PlanHistoryScreen() {
  const { data: plans, error } = useFocusData(() => api.planHistory());
  return (
    <Screen>
      <Banner message={error} />
      {plans?.length === 0 && <Muted>{t.noPlanYet}</Muted>}
      {plans?.map((plan) => (
        <Card key={plan.id} onPress={() => router.push(`/plan/${plan.id}`)}>
          <View style={styles.row}>
            <Text style={styles.name}>{t.planVersion(plan.version)}</Text>
            <Badge label={t.planStatus[plan.status]} tone={tone[plan.status]} />
          </View>
          <Muted>
            {t.planFor(
              t.goals[plan.goal_snapshot.training_goal],
              plan.goal_snapshot.days_per_week,
              plan.goal_snapshot.session_minutes,
            )}
          </Muted>
          <Muted>{t.createdOn(plan.created_at)}</Muted>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  name: { fontSize: 16, fontWeight: "700", color: colors.text },
});
