import { Stack } from "expo-router";

import { useAuth } from "@/auth/AuthContext";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";
import { isAdmin } from "@/lib/api";

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
      <Stack.Screen name="fitness" options={{ title: t.fitnessProfile }} />
      <Stack.Screen name="plan/index" options={{ title: t.myPlan }} />
      <Stack.Screen name="plan/history" options={{ title: t.planHistory }} />
      <Stack.Screen name="plan/[id]" options={{ title: "" }} />
      <Stack.Screen name="gyms/[id]" options={{ title: "" }} />
      <Stack.Protected guard={isAdmin(user)}>
        <Stack.Screen name="admin/index" options={{ title: t.admin }} />
        <Stack.Screen name="admin/gym-form" options={{ title: t.addGym }} />
        <Stack.Screen name="admin/members" options={{ title: t.members }} />
      </Stack.Protected>
    </Stack>
  );
}
