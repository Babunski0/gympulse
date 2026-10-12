import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Banner, Button, Field, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { validateCredentials, type FieldErrors } from "@/lib/validation";

export default function LoginScreen() {
  const { login } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    const errors = validateCredentials(email, password);
    setFieldErrors(errors);
    setError(null);
    if (Object.keys(errors).length) return;
    setLoading(true);
    try {
      await login(email.trim(), password);
    } catch (err) {
      setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <View style={styles.header}>
        <Text style={styles.title}>{t.appName}</Text>
        <Text style={styles.tagline}>{t.tagline}</Text>
      </View>
      <Banner message={error} />
      <Field
        label={t.email}
        value={email}
        onChangeText={setEmail}
        error={fieldErrors.email}
        autoCapitalize="none"
        autoComplete="email"
        keyboardType="email-address"
        textContentType="emailAddress"
      />
      <Field
        label={t.password}
        value={password}
        onChangeText={setPassword}
        error={fieldErrors.password}
        secureTextEntry
        autoComplete="current-password"
        textContentType="password"
        onSubmitEditing={submit}
      />
      <Button title={t.login} onPress={submit} loading={loading} />
      <Button title={t.noAccount} onPress={() => router.push("/register")} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  header: { marginTop: spacing.xl * 2, marginBottom: spacing.lg, gap: spacing.xs },
  title: { fontSize: 34, fontWeight: "800", color: colors.text },
  tagline: { fontSize: 16, color: colors.muted },
});
