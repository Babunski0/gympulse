import { useEffect, useRef } from "react";
import { StyleSheet, View } from "react-native";
import MapView, { Circle, Marker } from "react-native-maps";

import { colors } from "../theme";
import { DEFAULT_CENTER, type GymMapProps } from "./types";

const DELTA = 0.004; // roughly 400 m across: the radius circle stays readable

const FOCUS_DELTA = { city: 0.08, street: DELTA };

export function GymMap({ value, radiusM, onChange, focus, height = 260 }: GymMapProps) {
  const ref = useRef<MapView>(null);
  const center = value ?? DEFAULT_CENTER;

  // Follow the pin when it moves from outside the map (e.g. "use my location").
  useEffect(() => {
    if (value) {
      ref.current?.animateToRegion({ ...value, latitudeDelta: DELTA, longitudeDelta: DELTA }, 300);
    }
  }, [value?.latitude, value?.longitude]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (focus) {
      const d = FOCUS_DELTA[focus.zoom];
      ref.current?.animateToRegion({ ...focus.coords, latitudeDelta: d, longitudeDelta: d }, 400);
    }
  }, [focus]);

  return (
    <View style={[styles.wrap, { height }]}>
      <MapView
        ref={ref}
        style={StyleSheet.absoluteFill}
        initialRegion={{
          ...center,
          latitudeDelta: value ? DELTA : 0.05,
          longitudeDelta: value ? DELTA : 0.05,
        }}
        onPress={onChange ? (e) => onChange(e.nativeEvent.coordinate) : undefined}
        scrollEnabled
        zoomEnabled
      >
        {value && (
          <>
            <Circle
              center={value}
              radius={radiusM}
              strokeColor={colors.primary}
              strokeWidth={2}
              fillColor="rgba(31, 111, 235, 0.15)"
            />
            <Marker
              coordinate={value}
              draggable={!!onChange}
              onDragEnd={onChange ? (e) => onChange(e.nativeEvent.coordinate) : undefined}
            />
          </>
        )}
      </MapView>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { borderRadius: 12, overflow: "hidden", borderWidth: 1, borderColor: colors.border },
});
