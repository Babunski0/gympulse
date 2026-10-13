import { Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { MembershipBadge } from "@/components/MembershipBadge";
import { Banner, Button, Card, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, type Member, type MembershipStatus } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function MembersScreen() {
  const { gymId, name } = useLocalSearchParams<{ gymId: string; name?: string }>();
  const { data: members, error, setData } = useFocusData(() => api.listMembers(gymId), [gymId]);

  const [actionError, setActionError] = useState<string | null>(null);

  async function decide(member: Member, status: MembershipStatus) {
    setActionError(null);
    try {
      const updated = await api.setMembershipStatus(gymId, member.id, status);
      setData((members ?? []).map((m) => (m.id === member.id ? { ...m, status: updated.status } : m)));
    } catch (err) {
      setActionError(errorMessage(err));
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: name ? `${t.members}: ${name}` : t.members }} />
      <Banner message={error ?? actionError} />
      {members?.length === 0 && <Muted>{t.noMembers}</Muted>}
      {members?.map((m) => (
        <Card key={m.id}>
          <View style={styles.row}>
            <Text style={styles.name}>{m.full_name}</Text>
            <MembershipBadge status={m.status} />
          </View>
          <Muted>{m.email}</Muted>
          {(
            <View style={styles.actions}>
              {m.status !== "active" && (
                <View style={{ flex: 1 }}>
                  <Button title={t.approve} onPress={() => decide(m, "active")} />
                </View>
              )}
              {m.status !== "rejected" && (
                <View style={{ flex: 1 }}>
                  <Button title={t.reject} variant="ghost" onPress={() => decide(m, "rejected")} />
                </View>
              )}
            </View>
          )}
        </Card>
      ))}
    </Screen>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: spacing.sm },
  name: { fontSize: 16, fontWeight: "700", color: colors.text, flexShrink: 1 },
  actions: { flexDirection: "row", gap: spacing.sm, marginTop: spacing.xs },
});
