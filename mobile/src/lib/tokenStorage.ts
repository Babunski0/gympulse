import * as SecureStore from "expo-secure-store";
import { Platform } from "react-native";

const ACCESS_KEY = "gympulse.access_token";
const REFRESH_KEY = "gympulse.refresh_token";

export type Tokens = { accessToken: string; refreshToken: string };

// SecureStore (Keychain / Keystore) on phones; localStorage only for the web dev preview.
const store = {
  get: (key: string) =>
    Platform.OS === "web"
      ? Promise.resolve(globalThis.localStorage?.getItem(key) ?? null)
      : SecureStore.getItemAsync(key),
  set: (key: string, value: string) =>
    Platform.OS === "web"
      ? Promise.resolve(globalThis.localStorage?.setItem(key, value))
      : SecureStore.setItemAsync(key, value),
  remove: (key: string) =>
    Platform.OS === "web"
      ? Promise.resolve(globalThis.localStorage?.removeItem(key))
      : SecureStore.deleteItemAsync(key),
};

export async function loadTokens(): Promise<Tokens | null> {
  const [accessToken, refreshToken] = await Promise.all([store.get(ACCESS_KEY), store.get(REFRESH_KEY)]);
  return accessToken && refreshToken ? { accessToken, refreshToken } : null;
}

export async function saveTokens(tokens: Tokens): Promise<void> {
  await Promise.all([store.set(ACCESS_KEY, tokens.accessToken), store.set(REFRESH_KEY, tokens.refreshToken)]);
}

export async function clearTokens(): Promise<void> {
  await Promise.all([store.remove(ACCESS_KEY), store.remove(REFRESH_KEY)]);
}
