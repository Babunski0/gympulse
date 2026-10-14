import { errorMessage, t } from "@/i18n/sr";
import { api, ApiError, type Attendance } from "@/lib/api";
import { getCurrentLocation } from "@/lib/location";

export type CheckInResult = { ok: true; session: Attendance } | { ok: false; message: string };

/** Reads the phone's location once and lets the server decide if the user is at the gym. */
export async function checkInAt(gymId: string): Promise<CheckInResult> {
  const location = await getCurrentLocation();
  if (!location.ok) {
    const message = location.reason === "denied" ? t.checkInLocationDenied : t.checkInLocationUnavailable;
    return { ok: false, message };
  }
  try {
    const session = await api.checkIn(gymId, location.coords, location.accuracyM ?? 0);
    return { ok: true, session };
  } catch (err) {
    return { ok: false, message: checkInError(err) };
  }
}

function checkInError(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.code === "outside_gym_radius") {
      return t.tooFar(t.distance(Number(err.details.distance_m)), Number(err.details.radius_m));
    }
    if (err.code === "location_inaccurate") return t.locationNotPrecise(Number(err.details.accuracy_m));
    if (err.code === "forbidden") return t.checkInNeedsMembership;
  }
  return errorMessage(err);
}
