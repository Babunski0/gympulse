import type { ReactNode } from "react";
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type TextInputProps,
} from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

import { colors, spacing } from "./theme";

export function Screen({ children }: { children: ReactNode }) {
  return (
    <SafeAreaView style={styles.safe} edges={["bottom", "left", "right"]}>
      <ScrollView contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        {children}
      </ScrollView>
    </SafeAreaView>
  );
}

type FieldProps = TextInputProps & { label: string; error?: string; hint?: string };

export function Field({ label, error, hint, ...input }: FieldProps) {
  return (
    <View style={styles.field}>
      <Text style={styles.label}>{label}</Text>
      <TextInput
        style={[styles.input, error ? styles.inputError : null]}
        placeholderTextColor={colors.muted}
        accessibilityLabel={label}
        {...input}
      />
      {error ? <Text style={styles.errorText}>{error}</Text> : hint ? <Text style={styles.hint}>{hint}</Text> : null}
    </View>
  );
}

type ButtonProps = { title: string; onPress: () => void; loading?: boolean; variant?: "primary" | "ghost" };

export function Button({ title, onPress, loading, variant = "primary" }: ButtonProps) {
  const primary = variant === "primary";
  return (
    <Pressable
      accessibilityRole="button"
      onPress={onPress}
      disabled={loading}
      style={({ pressed }) => [
        styles.button,
        primary ? styles.buttonPrimary : styles.buttonGhost,
        (pressed || loading) && { opacity: 0.7 },
      ]}
    >
      {loading ? (
        <ActivityIndicator color={primary ? colors.primaryText : colors.primary} />
      ) : (
        <Text style={primary ? styles.buttonPrimaryText : styles.buttonGhostText}>{title}</Text>
      )}
    </Pressable>
  );
}

export function Banner({ message, tone = "error" }: { message: string | null; tone?: "error" | "success" }) {
  if (!message) return null;
  return (
    <Text accessibilityRole="alert" style={[styles.banner, tone === "error" ? styles.bannerError : styles.bannerSuccess]}>
      {message}
    </Text>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: colors.background },
  content: { padding: spacing.lg, gap: spacing.md, flexGrow: 1 },
  field: { gap: spacing.xs },
  label: { fontSize: 14, fontWeight: "600", color: colors.text },
  input: {
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    paddingHorizontal: spacing.md,
    paddingVertical: 12,
    fontSize: 16,
    color: colors.text,
  },
  inputError: { borderColor: colors.danger },
  errorText: { color: colors.danger, fontSize: 13 },
  hint: { color: colors.muted, fontSize: 13 },
  button: { borderRadius: 10, paddingVertical: 14, alignItems: "center", minHeight: 48, justifyContent: "center" },
  buttonPrimary: { backgroundColor: colors.primary },
  buttonGhost: { backgroundColor: "transparent" },
  buttonPrimaryText: { color: colors.primaryText, fontSize: 16, fontWeight: "600" },
  buttonGhostText: { color: colors.primary, fontSize: 15, fontWeight: "500" },
  banner: { padding: spacing.md, borderRadius: 10, fontSize: 14, overflow: "hidden" },
  bannerError: { backgroundColor: "#FDECEA", color: colors.danger },
  bannerSuccess: { backgroundColor: "#E8F5E9", color: colors.success },
});

export function Chip({ label, selected, onPress }: { label: string; selected?: boolean; onPress?: () => void }) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected }}
      onPress={onPress}
      style={[chipStyles.chip, selected && chipStyles.selected]}
    >
      <Text style={[chipStyles.text, selected && chipStyles.selectedText]}>{label}</Text>
    </Pressable>
  );
}

export function Badge({ label, tone }: { label: string; tone: "success" | "warning" | "muted" }) {
  const palette = {
    success: { bg: "#E8F5E9", fg: colors.success },
    warning: { bg: "#FFF4E5", fg: "#9A5B00" },
    muted: { bg: "#EEF0F3", fg: colors.muted },
  }[tone];
  return <Text style={[chipStyles.badge, { backgroundColor: palette.bg, color: palette.fg }]}>{label}</Text>;
}

export function Card({ children, onPress }: { children: ReactNode; onPress?: () => void }) {
  if (!onPress) return <View style={chipStyles.card}>{children}</View>;
  return (
    <Pressable onPress={onPress} style={({ pressed }) => [chipStyles.card, pressed && { opacity: 0.8 }]}>
      {children}
    </Pressable>
  );
}

export function SectionTitle({ children }: { children: ReactNode }) {
  return <Text style={chipStyles.section}>{children}</Text>;
}

export function Muted({ children }: { children: ReactNode }) {
  return <Text style={chipStyles.muted}>{children}</Text>;
}

const chipStyles = StyleSheet.create({
  chip: {
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderRadius: 999,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
  selected: { backgroundColor: colors.primary, borderColor: colors.primary },
  text: { color: colors.text, fontSize: 14, fontWeight: "500" },
  selectedText: { color: colors.primaryText },
  badge: {
    alignSelf: "flex-start",
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: 6,
    fontSize: 12,
    fontWeight: "600",
    overflow: "hidden",
  },
  card: {
    backgroundColor: colors.surface,
    borderRadius: 12,
    padding: spacing.md,
    gap: spacing.xs,
    borderWidth: 1,
    borderColor: colors.border,
  },
  section: { fontSize: 18, fontWeight: "700", color: colors.text, marginTop: spacing.sm },
  muted: { fontSize: 14, color: colors.muted, lineHeight: 20 },
});
