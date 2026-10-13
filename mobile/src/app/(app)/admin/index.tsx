import { router } from "expo-router";
import { StyleSheet, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { Badge, Banner, Button, Card, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function AdminScreen() {
  const { user } = useAuth();
  const isAppAdmin = user?.role === "app_admin";
  const { data: gyms, error } = useFocusData(() => api.managedGyms());

  return (
    <Screen>
      <Banner message={error} />
      {isAppAdmin && <Button title={t.addGym} onPress={() => router.push("/admin/gym-form")} />}
      <SectionTitle>{isAppAdmin ? t.allGyms : t.managedGyms}</SectionTitle>
      {gyms?.length === 0 && <Muted>{t.noManagedGyms}</Muted>}
      {gyms?.map((gym) => (
        <Card key={gym.id}>
          <View style={styles.row}>
            <Text style={styles.name}>{gym.name}</Text>
            {!gym.is_active && <Badge label={t.gymHidden} tone="muted" />}
          </View>
          <Muted>{gym.city ? `${gym.address}, ${gym.city}` : `${gym.address} · ${t.cityMissing}`}</Muted>
          <Muted>
            {t.radius}: {t.radiusValue(gym.radius_m)} ·{" "}
            {gym.maximum_capacity ? t.capacityValue(gym.maximum_capacity) : t.capacityNone}
          </Muted>
          <View style={styles.actions}>
            <View style={{ flex: 1 }}>
              <Button
                title={t.editGym}
                variant="ghost"
                onPress={() => router.push({ pathname: "/admin/gym-form", params: { id: gym.id } })}
              />
            </View>
            <View style={{ flex: 1 }}>
              <Button
                title={t.members}
                variant="ghost"
                onPress={() =>
                  router.push({ pathname: "/admin/members", params: { gymId: gym.id, name: gym.name } })
                }
              />
            </View>
          </View>
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  name: { fontSize: 16, fontWeight: "700", color: colors.text, flexShrink: 1 },
  actions: { flexDirection: "row", gap: spacing.sm },
});
