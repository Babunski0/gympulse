import { Tabs } from "expo-router";
import { Text } from "react-native";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";

function icon(symbol: string) {
  return ({ focused }: { focused: boolean }) => (
    <Text style={{ fontSize: 20, lineHeight: 24, opacity: focused ? 1 : 0.55 }}>{symbol}</Text>
  );
}

/** The four places a member goes most: home, training, gyms and their profile. */
export default function TabsLayout() {
  const insets = useSafeAreaInsets();
  return (
    <Tabs
      screenOptions={{
        headerShadowVisible: false,
        headerStyle: { backgroundColor: colors.background },
        headerTitleStyle: { color: colors.text, fontWeight: "700" },
        tabBarActiveTintColor: colors.primary,
        tabBarInactiveTintColor: colors.muted,
        tabBarLabelStyle: { fontSize: 12, lineHeight: 16, fontWeight: "600" },
        tabBarStyle: {
          backgroundColor: colors.surface,
          borderTopColor: colors.border,
          height: 70 + insets.bottom,
          paddingTop: 4,
          paddingBottom: 8 + insets.bottom,
        },
      }}
    >
      <Tabs.Screen name="index" options={{ title: t.tabHome, headerTitle: t.appName, tabBarIcon: icon("🏠") }} />
      <Tabs.Screen name="training" options={{ title: t.tabTraining, tabBarIcon: icon("🏋️") }} />
      <Tabs.Screen name="gyms" options={{ title: t.gyms, tabBarIcon: icon("📍") }} />
      <Tabs.Screen name="profile" options={{ title: t.profile, tabBarIcon: icon("👤") }} />
    </Tabs>
  );
}
