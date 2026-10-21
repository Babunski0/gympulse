import { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";

import { colors, spacing } from "./theme";

export type Bar = {
  key: string;
  value: number;
  label: string; // under the bar
  detail: string; // shown when the bar is tapped
  highlight?: boolean; // drawn darker, e.g. a personal record
};

/**
 * A single-series bar chart drawn with plain views, so it works the same on phones and the web.
 * Tapping a bar shows its exact value above the chart; the last bar is selected at first.
 */
export function BarChart({ bars, height = 140, format }: { bars: Bar[]; height?: number; format: (v: number) => string }) {
  const [selected, setSelected] = useState<string | null>(null);
  const max = Math.max(...bars.map((b) => b.value), 0);
  const active = bars.find((b) => b.key === selected) ?? bars[bars.length - 1];
  // Label only every few bars when there are many, so the dates never collide.
  const every = Math.ceil(bars.length / 8);

  return (
    <View>
      <Text style={styles.readout} accessibilityLiveRegion="polite">
        {active ? active.detail : ""}
      </Text>
      <View style={styles.plot}>
        <Text style={styles.axis}>{format(max)}</Text>
        <View style={[styles.bars, { height }]}>
          <View style={styles.gridTop} />
          {bars.map((b) => {
            const h = max > 0 ? Math.max((b.value / max) * height, b.value > 0 ? 3 : 0) : 0;
            const isActive = b.key === active?.key;
            return (
              <Pressable
                key={b.key}
                accessibilityRole="button"
                accessibilityLabel={b.detail}
                onPress={() => setSelected(b.key)}
                style={styles.slot}
              >
                <View
                  style={[
                    styles.bar,
                    { height: h },
                    b.highlight ? styles.barHighlight : null,
                    isActive ? styles.barActive : null,
                  ]}
                />
              </Pressable>
            );
          })}
        </View>
      </View>
      <View style={styles.labels}>
        {bars.map((b, i) => (
          <Text key={b.key} style={styles.label} numberOfLines={1}>
            {(bars.length - 1 - i) % every === 0 ? b.label : ""}
          </Text>
        ))}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  readout: { fontSize: 15, fontWeight: "700", color: colors.text, marginBottom: spacing.sm, minHeight: 20 },
  plot: { gap: 2 },
  axis: { fontSize: 11, color: colors.muted },
  bars: {
    flexDirection: "row",
    alignItems: "flex-end",
    gap: 2,
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  gridTop: { position: "absolute", top: 0, left: 0, right: 0, borderTopWidth: 1, borderTopColor: "#EEF0F3" },
  slot: { flex: 1, height: "100%", justifyContent: "flex-end", alignItems: "center" },
  bar: {
    width: "70%",
    maxWidth: 28,
    backgroundColor: "#9DBEF7",
    borderTopLeftRadius: 4,
    borderTopRightRadius: 4,
  },
  barHighlight: { backgroundColor: colors.primary },
  barActive: { borderWidth: 2, borderColor: colors.text },
  labels: { flexDirection: "row", gap: 2, marginTop: 4 },
  label: { flex: 1, fontSize: 10, color: colors.muted, textAlign: "center" },
});
