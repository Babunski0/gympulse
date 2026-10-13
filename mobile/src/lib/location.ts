import * as Location from "expo-location";

import type { Coords } from "@/components/map/types";

export type LocationResult =
  | { ok: true; coords: Coords; accuracyM: number | null }
  | { ok: false; reason: "denied" | "unavailable" };

/** One-off foreground location read; never tracks in the background (BR-02). */
export async function getCurrentLocation(): Promise<LocationResult> {
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
