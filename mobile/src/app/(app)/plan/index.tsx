import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { PlanView } from "@/components/PlanView";
import { Badge, Banner, Button, Card, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function PlanScreen() {
  const { data, error, setData } = useFocusData(async () => {
    const [profile, plans] = await Promise.all([api.getFitness(), api.currentPlans()]);
    return { profile, ...plans };
  });
  const [busy, setBusy] = useState<"generate" | "accept" | null>(null);
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);

  async function generate() {
    setBusy("generate");
    setMessage(null);
    try {
      const draft = await api.generatePlan();
      setData((prev) => prev && { ...prev, draft });
    } catch (err) {
      setMessage({ text: errorMessage(err), tone: "error" });
    } finally {
      setBusy(null);
    }
  }

  async function accept(id: string) {
    setBusy("accept");
    setMessage(null);
    try {
      const active = await api.acceptPlan(id);
      setData((prev) => prev && { ...prev, active, draft: null });
      setMessage({ text: t.planAccepted, tone: "success" });
    } catch (err) {
      setMessage({ text: errorMessage(err), tone: "error" });
    } finally {
      setBusy(null);
    }
  }

  if (!data) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }

  if (!data.profile) {
    return (
      <Screen>
        <Card>
          <Text style={styles.title}>{t.noProfileYet}</Text>
          <Button title={t.fillProfile} onPress={() => router.push("/fitness")} />
        </Card>
      </Screen>
    );
  }

  const { active, draft } = data;
  return (
    <Screen>
      <Banner message={message?.text ?? null} tone={message?.tone} />

      {draft && (
        <View style={styles.section}>
          <View style={styles.header}>
            <Text style={styles.title}>{t.draftTitle}</Text>
            <Badge label={t.planVersion(draft.version)} tone="warning" />
          </View>
          <Muted>{t.draftHint}</Muted>
          <Button title={t.acceptPlan} onPress={() => accept(draft.id)} loading={busy === "accept"} />
          <PlanView plan={draft} />
          <Button title={t.acceptPlan} onPress={() => accept(draft.id)} loading={busy === "accept"} />
        </View>
      )}

      {!draft && !active && (
        <Card>
          <Text style={styles.title}>{t.noPlanYet}</Text>
        </Card>
      )}

      {!draft && (
        <Button
          title={active ? t.makeNewPlan : t.makePlan}
          onPress={generate}
          loading={busy === "generate"}
          variant={active ? "ghost" : "primary"}
        />
      )}

      {active && !draft && (
        <View style={styles.section}>
          <View style={styles.header}>
            <Text style={styles.title}>{t.activePlanTitle}</Text>
            <Badge label={t.planVersion(active.version)} tone="success" />
          </View>
          <PlanView plan={active} />
        </View>
      )}

      {draft && (
        <Button title={t.makeNewPlan} onPress={generate} loading={busy === "generate"} variant="ghost" />
      )}
      <Button title={t.fitnessProfile} onPress={() => router.push("/fitness")} variant="ghost" />
      <Button title={t.planHistory} onPress={() => router.push("/plan/history")} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  section: { gap: spacing.md },
  header: { flexDirection: "row", alignItems: "center", justifyContent: "space-between", gap: spacing.sm },
  title: { fontSize: 20, fontWeight: "800", color: colors.text, flexShrink: 1 },
});
