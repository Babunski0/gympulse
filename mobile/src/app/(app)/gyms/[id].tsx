import { Stack, useLocalSearchParams } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { CurrentVisit } from "@/components/CurrentVisit";
import { MembershipBadge } from "@/components/MembershipBadge";
import { OccupancyMeter } from "@/components/OccupancyMeter";
import { GymMap } from "@/components/map/GymMap";
import { Banner, Button, Card, ConfirmButton, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { checkInAt } from "@/lib/checkIn";
import { useFocusData } from "@/lib/useFocusData";

// Occupancy is "live" by re-reading it while the screen is open.
const REFRESH_MS = 30_000;

export default function GymDetailsScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data, error, setData, reload } = useFocusData(
    async () => {
      const [gym, mine, visit] = await Promise.all([api.getGym(id), api.myGyms(), api.currentAttendance()]);
      return { gym, visit, membership: mine.find((m) => m.gym.id === id)?.membership ?? null };
    },
    [id],
    REFRESH_MS,
  );
  const [busy, setBusy] = useState<"join" | "leave" | "checkIn" | "checkOut" | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);
  const [notice, setNotice] = useState<string | null>(null);

  async function run(kind: NonNullable<typeof busy>, action: () => Promise<void>) {
    setBusy(kind);
    setActionError(null);
    setNotice(null);
    try {
      await action();
    } catch (err) {
      setActionError(errorMessage(err));
    } finally {
      setBusy(null);
    }
  }

  const join = () =>
    run("join", async () => {
      const membership = await api.joinGym(id);
      setData((prev) => prev && { ...prev, membership });
    });

  const leave = () =>
    run("leave", async () => {
      await api.leaveGym(id);
      setNotice(t.leftGym);
      await reload(); // membership, visit and occupancy all change
    });

  const checkIn = () =>
    run("checkIn", async () => {
      const result = await checkInAt(id);
      if (!result.ok) {
        setActionError(result.message);
        return;
      }
      setNotice(t.checkedInHere);
      await reload(); // occupancy now includes this member
    });

  const checkOut = () =>
    run("checkOut", async () => {
      const done = await api.checkOut();
      setNotice(t.checkedOut(t.duration(done.duration_minutes)));
      await reload();
    });

  if (!data) {
    return (
      <Screen>
        <Banner message={error} />
      </Screen>
    );
  }

  const { gym, membership, visit } = data;
  const canJoin = !membership || membership.status === "rejected";
  const visitHere = visit?.gym_id === gym.id ? visit : null;

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

      {gym.occupancy && (
        <Card>
          <SectionTitle>{t.occupancy}</SectionTitle>
          <OccupancyMeter occupancy={gym.occupancy} />
          <Muted>{t.occupancyUpdated}</Muted>
        </Card>
      )}

      <Banner message={actionError} />
      <Banner message={notice} tone="success" />
      {membership?.status === "active" &&
        (visitHere ? (
          <CurrentVisit session={visitHere} onCheckOut={checkOut} checkingOut={busy === "checkOut"} />
        ) : visit ? (
          <Muted>{t.checkedInElsewhere(visit.gym_name)}</Muted>
        ) : (
          <>
            <Button title={t.checkIn} onPress={checkIn} loading={busy === "checkIn"} />
            <Muted>{t.checkInHint(gym.radius_m)}</Muted>
          </>
        ))}
      {membership?.status === "pending" && <Muted>{t.joinedPending}</Muted>}
      {membership?.status === "pending" && <Muted>{t.checkInNeedsApproval}</Muted>}
      {membership?.status === "rejected" && <Muted>{t.joinedRejected}</Muted>}
      {canJoin && (
        <>
          <Muted>{t.checkInNeedsMembership}</Muted>
          <Button
            title={gym.membership_requires_approval ? t.requestJoin : t.join}
            onPress={join}
            loading={busy === "join"}
          />
        </>
      )}

      <GymMap value={gym} radiusM={gym.radius_m} />
      <View style={styles.facts}>
        <Fact label={t.radius} value={t.radiusValue(gym.radius_m)} />
        <Fact
          label={t.capacity}
          value={gym.maximum_capacity ? t.capacityValue(gym.maximum_capacity) : t.capacityNone}
        />
      </View>
      {membership && membership.status !== "rejected" && (
        <ConfirmButton
          title={membership.status === "pending" ? t.cancelRequest : t.leaveGym}
          question={membership.status === "pending" ? t.cancelRequestQuestion : t.leaveGymQuestion(gym.name)}
          confirmTitle={membership.status === "pending" ? t.cancelRequestConfirm : t.leaveGymConfirm}
          cancelTitle={t.cancel}
          onConfirm={leave}
          loading={busy === "leave"}
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
