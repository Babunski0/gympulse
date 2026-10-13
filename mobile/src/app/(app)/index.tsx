import { router } from "expo-router";
import { StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Button, Muted, Screen } from "@/components/ui";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";

export default function HomeScreen() {
  const { user } = useAuth();
  const firstName = user?.full_name.split(" ")[0] ?? "";

  return (
    <Screen>
      <Text style={styles.title}>{t.welcome(firstName)}</Text>
      <Muted>{t.homeComingSoon}</Muted>
      <Button title={t.gyms} onPress={() => router.push("/gyms")} />
      {user?.role === "gym_admin" && <Button title={t.admin} onPress={() => router.push("/admin")} />}
      <Button title={t.profile} onPress={() => router.push("/profile")} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 26, fontWeight: "800", color: colors.text },
});
