import { API_URL } from "./config";
import { clearTokens, loadTokens, saveTokens, type Tokens } from "./tokenStorage";

export type User = {
  id: string;
  email: string;
  full_name: string;
  role: "member" | "gym_admin" | "app_admin";
  created_at: string;
};

export type Gym = {
  id: string;
  name: string;
  address: string;
  city: string;
  latitude: number;
  longitude: number;
  radius_m: number;
  maximum_capacity: number | null;
  membership_requires_approval: boolean;
  is_active: boolean;
  occupancy?: Occupancy | null;
};

/** Live head count. Without a maximum capacity there is no percentage or level. */
export type Occupancy = {
  current: number;
  maximum_capacity: number | null;
  percent: number | null;
  level: "low" | "medium" | "high" | null;
};

export type Attendance = {
  id: string;
  gym_id: string;
  gym_name: string;
  check_in_at: string;
  check_out_at: string | null;
  close_reason: "user" | "auto_expired" | null;
  auto_close_at: string;
  duration_minutes: number;
};

export type GymInput = {
  name: string;
  address: string;
  city: string;
  latitude: number;
  longitude: number;
  radius_m: number;
  maximum_capacity: number | null;
  membership_requires_approval: boolean;
};

export type MembershipStatus = "pending" | "active" | "rejected";

export type Membership = {
  id: string;
  gym_id: string;
  user_id: string;
  status: MembershipStatus;
  created_at: string;
};

export type Member = Membership & { email: string; full_name: string };

export type MyGym = { gym: Gym; membership: Membership };

export const isAdmin = (user: User | null) => user?.role === "app_admin" || user?.role === "gym_admin";

type TokenResponse = { access_token: string; refresh_token: string };

/** Error shape returned by the backend: {"error": {"code", "message", "details?"}}. */
export class ApiError extends Error {
  constructor(
    public status: number,
    public code: string,
    message: string,
    public fields: Record<string, string> = {},
    public details: Record<string, unknown> = {},
  ) {
    super(message);
  }
}

let onSessionExpired: () => void = () => {};

/** Called by AuthProvider so the client can send the user back to login when refresh fails. */
export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler;
}

async function send(path: string, init: RequestInit, accessToken?: string): Promise<Response> {
  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (accessToken) headers.Authorization = `Bearer ${accessToken}`;
  try {
    return await fetch(`${API_URL}/api/v1${path}`, { ...init, headers });
  } catch {
    throw new ApiError(0, "network_error", "Network request failed");
  }
}

async function parse<T>(res: Response): Promise<T> {
  if (res.status === 204) return undefined as T;
  const body = await res.json().catch(() => null);
  if (res.ok) return body as T;
  const error = body?.error ?? {};
  // Validation errors list fields; other errors may carry extra facts such as a distance.
  const fields: Record<string, string> = {};
  const list = Array.isArray(error.details) ? error.details : [];
  for (const d of list) fields[d.field] = d.message;
  const details = error.details && !Array.isArray(error.details) ? error.details : {};
  throw new ApiError(res.status, error.code ?? "unknown_error", error.message ?? res.statusText, fields, details);
}

function toTokens(r: TokenResponse): Tokens {
  return { accessToken: r.access_token, refreshToken: r.refresh_token };
}

// One refresh at a time, even if several requests hit 401 together.
let refreshing: Promise<Tokens | null> | null = null;

async function refreshTokens(refreshToken: string): Promise<Tokens | null> {
  refreshing ??= (async () => {
    const res = await send("/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    });
    if (!res.ok) return null;
    const tokens = toTokens(await res.json());
    await saveTokens(tokens);
    return tokens;
  })().finally(() => {
    refreshing = null;
  });
  return refreshing;
}

/** Authenticated request; retries once with a refreshed token on 401. */
async function authed<T>(path: string, init: RequestInit = {}): Promise<T> {
  const tokens = await loadTokens();
  if (!tokens) {
    onSessionExpired();
    throw new ApiError(401, "unauthorized", "Not logged in");
  }
  let res = await send(path, init, tokens.accessToken);
  if (res.status === 401) {
    const fresh = await refreshTokens(tokens.refreshToken);
    if (!fresh) {
      await clearTokens();
      onSessionExpired();
      throw new ApiError(401, "unauthorized", "Session expired");
    }
    res = await send(path, init, fresh.accessToken);
  }
  return parse<T>(res);
}

export const api = {
  async register(email: string, password: string, fullName: string): Promise<User> {
    const res = await send("/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, full_name: fullName }),
    });
    return parse<User>(res);
  },

  async login(email: string, password: string): Promise<void> {
    const res = await send("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
    await saveTokens(toTokens(await parse<TokenResponse>(res)));
  },

  async logout(): Promise<void> {
    const tokens = await loadTokens();
    await clearTokens();
    if (tokens) {
      // Best effort: the local session is already gone even if the server is unreachable.
      await send("/auth/logout", { method: "POST" }, tokens.accessToken).catch(() => undefined);
    }
  },

  me: () => authed<User>("/me"),

  updateMe: (fullName: string) =>
    authed<User>("/me", { method: "PUT", body: JSON.stringify({ full_name: fullName }) }),

  listGyms: (filters: { q?: string; city?: string } = {}) => {
    const params = new URLSearchParams();
    if (filters.q) params.set("q", filters.q);
    if (filters.city) params.set("city", filters.city);
    const qs = params.toString();
    return authed<Gym[]>(`/gyms${qs ? `?${qs}` : ""}`);
  },
  listCities: () => authed<string[]>("/gyms/cities"),
  getGym: (id: string) => authed<Gym>(`/gyms/${id}`),
  myGyms: () => authed<MyGym[]>("/me/gyms"),
  joinGym: (id: string) => authed<Membership>(`/gyms/${id}/memberships`, { method: "POST" }),

  geocode: (q: string, kind: "city" | "address") =>
    authed<{ latitude: number; longitude: number; display_name: string }>(
      `/geocode?${new URLSearchParams({ q, kind }).toString()}`,
    ),

  getOccupancy: (id: string) => authed<Occupancy>(`/gyms/${id}/occupancy`),

  checkIn: (gymId: string, coords: { latitude: number; longitude: number }, accuracyM: number) =>
    authed<Attendance>("/attendance/check-in", {
      method: "POST",
      body: JSON.stringify({ gym_id: gymId, ...coords, accuracy_m: accuracyM }),
    }),
  checkOut: () => authed<Attendance>("/attendance/check-out", { method: "POST" }),
  currentAttendance: async () =>
    (await authed<{ session: Attendance | null }>("/attendance/current")).session,

  managedGyms: () => authed<Gym[]>("/admin/gyms"),
  createGym: (input: GymInput) => authed<Gym>("/gyms", { method: "POST", body: JSON.stringify(input) }),
  updateGym: (id: string, input: Partial<GymInput> & { is_active?: boolean }) =>
    authed<Gym>(`/gyms/${id}`, { method: "PATCH", body: JSON.stringify(input) }),
  listMembers: (gymId: string) => authed<Member[]>(`/gyms/${gymId}/memberships`),
  setMembershipStatus: (gymId: string, membershipId: string, status: MembershipStatus) =>
    authed<Membership>(`/gyms/${gymId}/memberships/${membershipId}`, {
      method: "PATCH",
      body: JSON.stringify({ status }),
    }),
};
