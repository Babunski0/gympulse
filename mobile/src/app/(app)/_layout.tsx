import { Stack } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";

export default function AppLayout() {
  const { user } = useAuth();
  return (
    <Stack
      screenOptions={{
        headerShadowVisible: false,
        headerStyle: { backgroundColor: colors.background },
        headerTintColor: colors.primary,
        headerTitleStyle: { color: colors.text },
        headerBackButtonDisplayMode: "minimal",
      }}
    >
      <Stack.Screen name="index" options={{ title: t.appName }} />
      <Stack.Screen name="profile" options={{ title: t.profile }} />
      <Stack.Screen name="gyms/index" options={{ title: t.gyms }} />
      <Stack.Screen name="gyms/[id]" options={{ title: "" }} />
      <Stack.Protected guard={user?.role === "gym_admin"}>
        <Stack.Screen name="admin/index" options={{ title: t.admin }} />
        <Stack.Screen name="admin/gym-form" options={{ title: t.addGym }} />
        <Stack.Screen name="admin/members" options={{ title: t.members }} />
      </Stack.Protected>
    </Stack>
  );
}
