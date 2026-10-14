import { StyleSheet, Text } from "react-native";

import { t } from "@/i18n/sr";
import type { Attendance } from "@/lib/api";

import { colors } from "./theme";
import { Button, Card, Muted } from "./ui";

/** "You are at X since 18:05" with the check-out button (ATT-06). */
export function CurrentVisit({
  session,
  onCheckOut,
  checkingOut,
}: {
  session: Attendance;
  onCheckOut: () => void;
  checkingOut: boolean;
}) {
  return (
    <Card>
      <Text style={styles.title}>{t.youAreHere(session.gym_name)}</Text>
      <Text style={styles.since}>
        {t.hereSince(t.clock(session.check_in_at), t.duration(session.duration_minutes))}
      </Text>
      <Muted>{t.autoCloseAt(t.clock(session.auto_close_at))}</Muted>
      <Button title={t.checkOut} onPress={onCheckOut} loading={checkingOut} />
    </Card>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 18, fontWeight: "700", color: colors.success },
  since: { fontSize: 15, color: colors.text },
});
