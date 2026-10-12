import { Stack } from "expo-router";

import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";

export default function AppLayout() {
  return (
    <Stack
      screenOptions={{
        headerShadowVisible: false,
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.primary,
        headerTitleStyle: { color: colors.text },
      }}
    >
      <Stack.Screen name="index" options={{ title: t.appName }} />
      <Stack.Screen name="profile" options={{ title: t.profile }} />
    </Stack>
  );
}
