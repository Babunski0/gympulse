import { Stack, useLocalSearchParams } from "expo-router";

import { PlanView } from "@/components/PlanView";
import { Banner, Muted, Screen } from "@/components/ui";
import { t } from "@/i18n/sr";
import { api } from "@/lib/api";
import { useFocusData } from "@/lib/useFocusData";

export default function PlanVersionScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const { data: plan, error } = useFocusData(() => api.getPlan(id), [id]);
  return (
    <Screen>
      <Banner message={error} />
      {plan && (
        <>
          <Stack.Screen options={{ title: `${t.planVersion(plan.version)} · ${t.planStatus[plan.status]}` }} />
          <Muted>{t.createdOn(plan.created_at)}</Muted>
          <PlanView plan={plan} />
        </>
      )}
    </Screen>
  );
}
