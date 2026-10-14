import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Banner, Button, Card, Field, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, isAdmin } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function ProfileScreen() {
  const { user, setUser, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [nameError, setNameError] = useState<string | undefined>();
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);
  const [saving, setSaving] = useState(false);
  const { data: fitness } = useFocusData(() => api.getFitness());

  if (!user) return null;

  async function save() {
    setMessage(null);
    if (!fullName.trim()) {
      setNameError(t.required);
      return;
    }
    setNameError(undefined);
    setSaving(true);
    try {
      setUser(await api.updateMe(fullName.trim()));
      setMessage({ text: t.saved, tone: "success" });
    } catch (err) {
      setMessage({ text: errorMessage(err), tone: "error" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Screen>
      <SectionTitle>{t.fitnessProfile}</SectionTitle>
      <Card onPress={() => router.push("/fitness")}>
        {fitness ? (
          <>
            <Text style={styles.value}>
              {t.fitnessSummary(t.goals[fitness.training_goal], fitness.days_per_week, fitness.session_minutes)}
            </Text>
            <Muted>
              {t.experiences[fitness.experience_level]}
              {fitness.weight_kg ? ` · ${String(fitness.weight_kg).replace(".", ",")} kg` : ""}
            </Muted>
          </>
        ) : (
          <Muted>{t.fitnessMissing}</Muted>
        )}
        <Text style={styles.link}>{t.edit} →</Text>
      </Card>
      {isAdmin(user) && <Button title={`⚙️  ${t.admin}`} onPress={() => router.push("/admin")} />}
      <SectionTitle>{t.account}</SectionTitle>
      <View style={styles.card}>
        <Text style={styles.label}>{t.email}</Text>
        <Text style={styles.value}>{user.email}</Text>
        <Text style={styles.label}>{t.memberSince}</Text>
        <Text style={styles.value}>{new Date(user.created_at).toLocaleDateString("sr-Latn")}</Text>
      </View>
      <Banner message={message?.text ?? null} tone={message?.tone} />
      <Field label={t.fullName} value={fullName} onChangeText={setFullName} error={nameError} />
      <Button title={t.save} onPress={save} loading={saving} />
      <View style={{ flex: 1 }} />
      <Button title={t.logout} onPress={logout} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  card: { backgroundColor: colors.surface, borderRadius: 12, padding: spacing.md, gap: spacing.xs },
  label: { fontSize: 13, color: colors.muted },
  value: { fontSize: 16, color: colors.text, marginBottom: spacing.sm },
  link: { fontSize: 15, fontWeight: "600", color: colors.primary },
});
