import Constants from "expo-constants";
import { Platform } from "react-native";

const API_PORT = 8000;

/**
 * Where the backend lives. EXPO_PUBLIC_API_URL wins; otherwise use the computer that serves
 * the Expo bundle (so a phone on the same Wi-Fi reaches the API without extra setup).
 */
function resolveApiUrl(): string {
  const fromEnv = process.env.EXPO_PUBLIC_API_URL;
  if (fromEnv) return fromEnv.replace(/\/$/, "");

  const devHost = Constants.expoConfig?.hostUri?.split(":")[0];
  if (devHost) return `http://${devHost}:${API_PORT}`;

  // Android emulator reaches the host machine through 10.0.2.2.
  const host = Platform.OS === "android" ? "10.0.2.2" : "localhost";
  return `http://${host}:${API_PORT}`;
}

export const API_URL = resolveApiUrl();
