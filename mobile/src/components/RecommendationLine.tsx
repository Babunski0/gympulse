import { StyleSheet, Text, View } from "react-native";

import { t } from "@/i18n/sr";
import type { Recommendation } from "@/lib/api";

import { colors, spacing } from "./theme";

/** "💡 Preporuka: 40 kg × 8 ponavljanja" with a short reason underneath. */
export function RecommendationLine({
  rec,
  unit,
  showReason = true,
}: {
  rec: Recommendation;
  unit: string;
  showReason?: boolean;
}) {
  const what =
    rec.weight_kg === null
      ? t.recReps(rec.reps, unit)
      : `${t.recWeight(rec.weight_kg, rec.per_hand)} × ${t.recReps(rec.reps, unit)}`;
  const why =
    rec.weight_kg === null && rec.basis === "increase" ? t.recWhyBodyweightMax : t.recWhy[rec.basis];
  return (
    <View style={styles.box}>
      <Text style={styles.main}>
        💡 {t.recommended}: <Text style={styles.value}>{what}</Text>
      </Text>
      {showReason && <Text style={styles.why}>{why}</Text>}
      {showReason && rec.estimated_from_default_weight && <Text style={styles.why}>{t.recNoBodyWeight}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  box: { backgroundColor: "#EEF4FF", borderRadius: 10, padding: spacing.sm, gap: 2 },
  main: { fontSize: 14, color: colors.text },
  value: { fontWeight: "700", color: colors.primary },
  why: { fontSize: 13, color: colors.muted, lineHeight: 18 },
});
