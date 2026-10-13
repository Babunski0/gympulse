import { router } from "expo-router";
import { useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { MembershipBadge } from "@/components/MembershipBadge";
import { Banner, Card, Chip, Field, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors } from "@/components/theme";
import { t } from "@/i18n/sr";
import { api, type Gym, type MembershipStatus } from "@/lib/api";
import { useDebounced } from "@/lib/useDebounced";
import { useFocusData } from "@/lib/useFocusData";

export default function GymsScreen() {
  const [query, setQuery] = useState("");
  const [city, setCity] = useState<string | null>(null);
  const search = useDebounced(query.trim());
  const { data, error } = useFocusData(
    async () => {
      const [gyms, mine, cities] = await Promise.all([
        api.listGyms({ q: search || undefined, city: city ?? undefined }),
        api.myGyms(),
        api.listCities(),
      ]);
      const status = new Map(mine.map((m) => [m.gym.id, m.membership.status]));
      return { gyms, mine, status, cities };
    },
    [search, city],
  );

  return (
    <Screen>
      <Banner message={error} />
      {data && data.mine.length > 0 && (
        <>
          <SectionTitle>{t.myGyms}</SectionTitle>
          {data.mine.map(({ gym, membership }) => (
            <GymRow key={gym.id} gym={gym} status={membership.status} />
          ))}
        </>
      )}
      <SectionTitle>{t.findGym}</SectionTitle>
      <Field
        label={t.searchGyms}
        value={query}
        onChangeText={setQuery}
        placeholder="npr. Pulse"
        autoCorrect={false}
      />
      {data && data.cities.length > 0 && (
        <View style={styles.chips}>
          <Chip label={t.allCities} selected={city === null} onPress={() => setCity(null)} />
          {data.cities.map((c) => (
            <Chip key={c} label={c} selected={city === c} onPress={() => setCity(c)} />
          ))}
        </View>
      )}
      {data?.gyms.length === 0 && <Muted>{t.noGymsFound}</Muted>}
      {data?.gyms
        .filter((g) => !data.status.has(g.id))
        .map((gym) => <GymRow key={gym.id} gym={gym} />)}
    </Screen>
  );
}

function GymRow({ gym, status }: { gym: Gym; status?: MembershipStatus }) {
  return (
    <Card onPress={() => router.push(`/gyms/${gym.id}`)}>
      <View style={styles.row}>
        <Text style={styles.name}>{gym.name}</Text>
        {status && <MembershipBadge status={status} />}
      </View>
      <Muted>
        {gym.address}, {gym.city}
      </Muted>
    </Card>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", gap: 8 },
  name: { fontSize: 16, fontWeight: "700", color: colors.text, flexShrink: 1 },
});
