import { Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { MembershipBadge } from "@/components/MembershipBadge";
import { GymMap } from "@/components/map/GymMap";
import { Banner, Button, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function GymDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data, error, setData } = useFocusData(async () => {
    const [gym, mine] = await Promise.all([api.getGym(id), api.myGyms()]);
    return { gym, membership: mine.find((m) => m.gym.id === id)?.membership ?? null };
  }, [id]);
  const [joining, setJoining] = useState(false);
  const [joinError, setJoinError] = useState<string | null>(null);

  async function join() {
    if (!data) return;
    setJoining(true);
    setJoinError(null);
    try {
      const membership = await api.joinGym(data.gym.id);
      setData({ ...data, membership });
    } catch (err) {
      setJoinError(errorMessage(err));
    } finally {
      setJoining(false);
    }
  }

  if (!data) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }

  const { gym, membership } = data;
  const canJoin = !membership || membership.status === "rejected";

  return (
    <Screen>
      <Stack.Screen options={{ title: gym.name }} />
      <View style={styles.header}>
        <Text style={styles.name}>{gym.name}</Text>
        {membership && <MembershipBadge status={membership.status} />}
      </View>
      <Muted>
        {gym.address}, {gym.city}
      </Muted>
      <GymMap value={gym} radiusM={gym.radius_m} />
      <Muted>{t.checkInHint(gym.radius_m)}</Muted>
      <View style={styles.facts}>
        <Fact label={t.radius} value={t.radiusValue(gym.radius_m)} />
        <Fact
          label={t.capacity}
          value={gym.maximum_capacity ? t.capacityValue(gym.maximum_capacity) : t.capacityNone}
        />
      </View>
      <Banner message={joinError} />
      {membership?.status === "active" && <Banner message={t.joinedActive} tone="success" />}
      {membership?.status === "pending" && <Muted>{t.joinedPending}</Muted>}
      {membership?.status === "rejected" && <Muted>{t.joinedRejected}</Muted>}
      {canJoin && (
        <Button
          title={gym.membership_requires_approval ? t.requestJoin : t.join}
          onPress={join}
          loading={joining}
        />
      )}
    </Screen>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <View style={styles.fact}>
      <Text style={styles.factLabel}>{label}</Text>
      <Text style={styles.factValue}>{value}</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  header: { flexDirection: "row", alignItems: "center", gap: spacing.sm, flexWrap: "wrap" },
  name: { fontSize: 24, fontWeight: "800", color: colors.text },
  facts: { flexDirection: "row", gap: spacing.sm },
  fact: { flex: 1, backgroundColor: colors.surface, borderRadius: 12, padding: spacing.md, gap: 2 },
  factLabel: { fontSize: 13, color: colors.muted },
  factValue: { fontSize: 16, fontWeight: "600", color: colors.text },
});
