import { StyleSheet, Text, View } from "react-native";

import { t } from "@/i18n/sr";
import type { Occupancy } from "@/lib/api";

import { colors, spacing } from "./theme";

const levelColor = { low: colors.success, medium: colors.warning, high: colors.danger };

/** Live head count. The bar and percentage appear only when the gym has a maximum capacity. */
export function OccupancyMeter({ occupancy, compact }: { occupancy: Occupancy; compact?: boolean }) {
  const { current, maximum_capacity: max, percent, level } = occupancy;
  const color = level ? levelColor[level] : colors.primary;
  const label = max ? t.occupancyCount(current, max) : t.occupancyPeople(current);

  return (
    <View style={styles.wrap} accessibilityLabel={`${t.occupancy}: ${label}`}>
      <View style={styles.row}>
        <Text style={[styles.count, compact && styles.countCompact]}>{label}</Text>
        {level && (
          <Text style={[styles.level, { color }]}>
            {t.occupancyLevel[level]} · {percent}%
          </Text>
        )}
      </View>
      {percent !== null && (
        <View style={[styles.track, compact && styles.trackCompact]}>
          <View style={[styles.fill, { width: `${Math.min(percent, 100)}%`, backgroundColor: color }]} />
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.xs },
  row: { flexDirection: "row", justifyContent: "space-between", alignItems: "baseline", gap: spacing.sm, flexWrap: "wrap" },
  count: { fontSize: 18, fontWeight: "700", color: colors.text },
  countCompact: { fontSize: 14, fontWeight: "600" },
  level: { fontSize: 13, fontWeight: "600" },
  track: { height: 10, borderRadius: 5, backgroundColor: colors.border, overflow: "hidden" },
  trackCompact: { height: 6, borderRadius: 3 },
  fill: { height: "100%", borderRadius: 5 },
});
