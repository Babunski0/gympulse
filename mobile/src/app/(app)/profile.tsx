import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Banner, Button, Field, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api } from "@/lib/api";

export default function ProfileScreen() {
  const { user, setUser, logout } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [nameError, setNameError] = useState<string | undefined>();
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);
  const [saving, setSaving] = useState(false);

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
});
