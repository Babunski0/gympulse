import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { CurrentVisit } from "@/components/CurrentVisit";
import { Banner, Button, Card, Muted, Screen } from "@/components/ui";
import { colors } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, isAdmin } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function HomeScreen() {
  const { user, logout } = useAuth();
  const firstName = user?.full_name.split(" ")[0] ?? "";
  // Refreshed every minute so the visit length keeps counting.
  const { data, error, setData, reload } = useFocusData(
    async () => {
      const [visit, workout] = await Promise.all([api.currentAttendance(), api.currentWorkout()]);
      return { visit, workout };
    },
    [],
    60_000,
  );
  const [checkingOut, setCheckingOut] = useState(false);
  const [notice, setNotice] = useState<string | null>(null);
  const [checkOutError, setCheckOutError] = useState<string | null>(null);

  async function checkOut() {
    setCheckingOut(true);
    setCheckOutError(null);
    try {
      const done = await api.checkOut();
      setData((d) => d && { ...d, visit: null });
      setNotice(t.checkedOut(t.duration(done.duration_minutes)));
    } catch (err) {
      setCheckOutError(errorMessage(err));
      void reload();
    } finally {
      setCheckingOut(false);
    }
  }

  return (
    <Screen>
      <Text style={styles.title}>{t.welcome(firstName)}</Text>
      <Banner message={error ?? checkOutError} />
      <Banner message={notice} tone="success" />
      {data?.visit && <CurrentVisit session={data.visit} onCheckOut={checkOut} checkingOut={checkingOut} />}
      {data && !data.visit && (
        <Card>
          <Text style={styles.cardTitle}>{t.notCheckedIn}</Text>
          <Muted>{t.notCheckedInHint}</Muted>
        </Card>
      )}
      {data?.workout ? (
        <Card onPress={() => router.push(`/workout/${data.workout!.id}`)}>
          <Text style={styles.cardTitle}>{t.workoutInProgress}</Text>
          <Muted>
            {data.workout.plan_day_name ?? t.freeWorkout} ·{" "}
            {t.workoutStartedAt(t.clock(data.workout.started_at), t.duration(data.workout.duration_minutes))}
          </Muted>
          <Text style={styles.link}>{t.continueWorkout} →</Text>
        </Card>
      ) : (
        data && <Button title={t.startWorkout} onPress={() => router.push("/workout/start")} />
      )}
      <Button title={t.gyms} onPress={() => router.push("/gyms")} />
      <Button title={t.myPlan} onPress={() => router.push("/plan")} />
      <Button title={t.workoutHistory} onPress={() => router.push("/workout/history")} variant="ghost" />
      <Button title={t.fitnessProfile} onPress={() => router.push("/fitness")} variant="ghost" />
      {isAdmin(user) && <Button title={t.admin} onPress={() => router.push("/admin")} />}
      <Muted>{t.homeComingSoon}</Muted>
      <Button title={t.profile} onPress={() => router.push("/profile")} variant="ghost" />
      <Button title={t.logout} onPress={logout} variant="ghost" />
    </Screen>
  );
}

const styles = StyleSheet.create({
  title: { fontSize: 26, fontWeight: "800", color: colors.text },
  cardTitle: { fontSize: 16, fontWeight: "600", color: colors.text },
  link: { fontSize: 15, fontWeight: "600", color: colors.primary },
});
