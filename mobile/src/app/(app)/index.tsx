import { router } from "expo-router";
import { StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Button, Screen } from "@/components/ui";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";

export default function HomeScreen() {
  const { user } = useAuth();
  const firstName = user?.full_name.split(" ")[0] ?? "";

  return (
    <Screen>
      <Text style={styles.title}>{t.welcome(firstName)}</Text>
      <Text style={styles.body}>{t.homeComingSoon}</Text>
      <Button title={t.profile} onPress={() => router.push("/profile")} />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 26, fontWeight: "800", color: colors.text },
  body: { fontSize: 16, color: colors.muted, lineHeight: 22 },
});
