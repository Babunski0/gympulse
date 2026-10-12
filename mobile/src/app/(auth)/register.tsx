import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Banner, Button, Field, Screen } from "@/components/ui";
import { colors } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { ApiError } from "@/lib/api";
import { validateCredentials, type FieldErrors } from "@/lib/validation";

export default function RegisterScreen() {
  const { register } = useAuth();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldErrors>({});
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function submit() {
    const errors = validateCredentials(email, password, fullName);
    setFieldErrors(errors);
    setError(null);
    if (Object.keys(errors).length) return;
    setLoading(true);
    try {
      await register(email.trim(), password, fullName.trim());
    } catch (err) {
      if (err instanceof ApiError && err.code === "email_taken") setFieldErrors({ email: errorMessage(err) });
      else setError(errorMessage(err));
    } finally {
      setLoading(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>{t.register}</Text>
      <Banner message={error} />
      <Field
        label={t.fullName}
        value={fullName}
        onChangeText={setFullName}
        error={fieldErrors.full_name}
        autoComplete="name"
        textContentType="name"
      />
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
        hint={t.passwordHint}
        secureTextEntry
        autoComplete="new-password"
        textContentType="newPassword"
        onSubmitEditing={submit}
      />
      <Button title={t.register} onPress={submit} loading={loading} />
      <Button title={t.haveAccount} onPress={() => router.back()} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 28, fontWeight: "800", color: colors.text },
});
