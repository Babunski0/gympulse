import * as Location from "expo-location";
import { Platform } from "react-native";

import type { Coords } from "@/components/map/types";

export type LocationResult =
  | { ok: true; coords: Coords; accuracyM: number | null }
  | { ok: false; reason: "denied" | "unavailable" };

/** One-off foreground location read; never tracks in the background (BR-02). */
export async function getCurrentLocation(): Promise<LocationResult> {
  if (Platform.OS === "web") return getBrowserLocation();
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== Location.PermissionStatus.GRANTED) return { ok: false, reason: "denied" };
  try {
    const pos = await Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.High });
    return {
      ok: true,
      coords: { latitude: pos.coords.latitude, longitude: pos.coords.longitude },
      accuracyM: pos.coords.accuracy,
    };
  } catch {
    return { ok: false, reason: "unavailable" };
  }
}

/**
 * expo-location on web reuses the first position it ever got (maximumAge: Infinity), so someone
 * who opened the app at home and then walked to the gym would still be "at home". Ask the
 * browser for a fresh fix instead.
 */
function getBrowserLocation(): Promise<LocationResult> {
  return new Promise((resolve) => {
    if (!navigator.geolocation) return resolve({ ok: false, reason: "unavailable" });
    navigator.geolocation.getCurrentPosition(
      (pos) =>
        resolve({
          ok: true,
          coords: { latitude: pos.coords.latitude, longitude: pos.coords.longitude },
          accuracyM: pos.coords.accuracy,
        }),
      (err) => resolve({ ok: false, reason: err.code === err.PERMISSION_DENIED ? "denied" : "unavailable" }),
      { enableHighAccuracy: true, maximumAge: 0, timeout: 15_000 },
    );
  });
}
