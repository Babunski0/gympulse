import { Stack, router, useLocalSearchParams } from "expo-router";
import { useEffect, useRef, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";

import { useAuth } from "@/auth/AuthContext";
import { GymMap } from "@/components/map/GymMap";
import type { Coords, MapFocus } from "@/components/map/types";
import { Banner, Button, Chip, ConfirmButton, Field, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, ApiError, type GymInput } from "@/lib/api";
import { getCurrentLocation } from "@/lib/location";
import { useDebounced } from "@/lib/useDebounced";

const RADIUS_PRESETS = [25, 50, 100, 150, 200];
const DEFAULT_RADIUS = 50;

type Errors = Partial<Record<"name" | "address" | "city" | "location" | "radius" | "capacity", string>>;

export default function GymFormScreen() {
  const { id } = useLocalSearchParams<{ id?: string }>();
  const editing = !!id;

  const [name, setName] = useState("");
  const [address, setAddress] = useState("");
  const [city, setCity] = useState("");
  const [coords, setCoords] = useState<Coords | null>(null);
  const [radius, setRadius] = useState(DEFAULT_RADIUS);
  const [radiusText, setRadiusText] = useState("");
  const [capacityText, setCapacityText] = useState("");
  const [requiresApproval, setRequiresApproval] = useState(false);
  const [isActive, setIsActive] = useState(true);

  const [errors, setErrors] = useState<Errors>({});
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);
  const [saving, setSaving] = useState(false);
  const [locating, setLocating] = useState(false);

  // Typing a city moves the map there; typing an address places the pin on it.
  // Only reacts to what the admin types, not to values loaded for editing.
  const [focus, setFocus] = useState<MapFocus | null>(null);
  const [mapNote, setMapNote] = useState<{ text: string; tone: "muted" | "error" } | null>(null);
  const edited = useRef({ city: false, address: false });
  const lookup = useRef(0);
  const typedCity = useDebounced(city.trim(), 800);
  const typedAddress = useDebounced(address.trim(), 900);

  async function findOnMap(query: string, kind: "city" | "address") {
    const ticket = ++lookup.current;
    setMapNote({ text: t.searchingMap, tone: "muted" });
    try {
      const hit = await api.geocode(query, kind);
      if (ticket !== lookup.current) return; // a newer search started meanwhile
      const found = { latitude: hit.latitude, longitude: hit.longitude };
      if (kind === "city") {
        setFocus({ coords: found, zoom: "city" });
        setMapNote({ text: t.cityFound(hit.display_name), tone: "muted" });
      } else {
        setCoords(found);
        setErrors((e) => ({ ...e, location: undefined }));
        setMapNote({ text: t.addressFound, tone: "muted" });
      }
    } catch (err) {
      if (ticket !== lookup.current) return;
      const code = err instanceof ApiError ? err.code : "";
      const text =
        code === "location_not_found"
          ? kind === "city"
            ? t.cityNotFound
            : t.addressNotFound
          : t.geocodingUnavailable;
      setMapNote({ text, tone: "error" });
    }
  }

  useEffect(() => {
    if (!edited.current.city || typedCity.length < 2) return;
    // With an address already typed, the address search below places the pin instead.
    if (typedAddress && edited.current.address) void findOnMap(`${typedAddress}, ${typedCity}`, "address");
    else void findOnMap(typedCity, "city");
  }, [typedCity]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!edited.current.address || typedAddress.length < 3) return;
    void findOnMap(typedCity ? `${typedAddress}, ${typedCity}` : typedAddress, "address");
  }, [typedAddress]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (!id) return;
    api
      .getGym(id)
      .then((gym) => {
        setName(gym.name);
        setAddress(gym.address);
        setCity(gym.city);
        setCoords({ latitude: gym.latitude, longitude: gym.longitude });
        setRadius(gym.radius_m);
        if (!RADIUS_PRESETS.includes(gym.radius_m)) setRadiusText(String(gym.radius_m));
        setCapacityText(gym.maximum_capacity ? String(gym.maximum_capacity) : "");
        setRequiresApproval(gym.membership_requires_approval);
        setIsActive(gym.is_active);
      })
      .catch((err) => setMessage({ text: errorMessage(err), tone: "error" }));
  }, [id]);

  async function useMyLocation() {
    setLocating(true);
    setMessage(null);
    const result = await getCurrentLocation();
    setLocating(false);
    if (result.ok) {
      setCoords(result.coords);
      setErrors((e) => ({ ...e, location: undefined }));
      if (result.accuracyM) setMessage({ text: t.myLocationAccuracy(result.accuracyM), tone: "success" });
    } else {
      setMessage({ text: result.reason === "denied" ? t.locationDenied : t.locationUnavailable, tone: "error" });
    }
  }

  function onCustomRadius(text: string) {
    setRadiusText(text);
    const n = Number(text);
    if (text && Number.isInteger(n)) setRadius(n);
  }

  function validate(): GymInput | null {
    const e: Errors = {};
    if (!name.trim()) e.name = t.required;
    if (!address.trim()) e.address = t.required;
    if (!city.trim()) e.city = t.required;
    if (!coords) e.location = t.locationMissing;
    if (!Number.isInteger(radius) || radius < 25 || radius > 2000) e.radius = t.radiusOutOfRange;
    let capacity: number | null = null;
    if (capacityText.trim()) {
      capacity = Number(capacityText);
      if (!Number.isInteger(capacity) || capacity < 1 || capacity > 10000) e.capacity = t.capacityInvalid;
    }
    setErrors(e);
    if (Object.keys(e).length || !coords) return null;
    return {
      name: name.trim(),
      address: address.trim(),
      city: city.trim(),
      latitude: coords.latitude,
      longitude: coords.longitude,
      radius_m: radius,
      maximum_capacity: capacity,
      membership_requires_approval: requiresApproval,
    };
  }

  const { user } = useAuth();
  const [deleting, setDeleting] = useState(false);

  async function remove() {
    if (!id) return;
    setDeleting(true);
    try {
      await api.deleteGym(id);
      router.back();
    } catch (err) {
      setMessage({ text: errorMessage(err), tone: "error" });
      setDeleting(false);
    }
  }

  async function save() {
    setMessage(null);
    const input = validate();
    if (!input) return;
    setSaving(true);
    try {
      if (id) await api.updateGym(id, { ...input, is_active: isActive });
      else await api.createGym(input);
      router.back();
    } catch (err) {
      const fields = err instanceof ApiError ? err.fields : {};
      setErrors({
        name: fields.name,
        address: fields.address,
        city: fields.city,
        radius: fields.radius_m && t.radiusOutOfRange,
        capacity: fields.maximum_capacity && t.capacityInvalid,
      });
      setMessage({ text: errorMessage(err), tone: "error" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Screen>
      <Stack.Screen options={{ title: editing ? t.editGym : t.addGym }} />
      <Field label={t.gymName} value={name} onChangeText={setName} error={errors.name} />
      <Field
        label={t.city}
        value={city}
        onChangeText={(v) => {
          edited.current.city = true;
          setCity(v);
        }}
        error={errors.city}
        placeholder="npr. Podgorica"
      />
      <Field
        label={t.address}
        value={address}
        onChangeText={(v) => {
          edited.current.address = true;
          setAddress(v);
        }}
        error={errors.address}
        placeholder="npr. Bulevar Džordža Vašingtona 10"
      />

      <Text style={styles.label}>{t.location}</Text>
      <Muted>{t.locationHint}</Muted>
      <GymMap
        value={coords}
        radiusM={radius >= 25 && radius <= 2000 ? radius : DEFAULT_RADIUS}
        height={320}
        focus={focus}
        onChange={(c) => {
          lookup.current++; // a manual pin wins over a search still in flight
          setCoords(c);
          setMapNote(null);
          setErrors((e) => ({ ...e, location: undefined }));
        }}
      />
      {mapNote && (
        <Text style={mapNote.tone === "error" ? styles.error : styles.note}>{mapNote.text}</Text>
      )}
      {coords ? (
        <Muted>{t.coordinates(coords.latitude, coords.longitude)}</Muted>
      ) : (
        errors.location && <Text style={styles.error}>{errors.location}</Text>
      )}
      <Button title={t.useMyLocation} onPress={useMyLocation} loading={locating} variant="ghost" />

      <Text style={styles.label}>{t.radius}</Text>
      <View style={styles.chips}>
        {RADIUS_PRESETS.map((r) => (
          <Chip
            key={r}
            label={t.radiusValue(r)}
            selected={radius === r && !radiusText}
            onPress={() => {
              setRadius(r);
              setRadiusText("");
            }}
          />
        ))}
      </View>
      <Field
        label={t.customRadius}
        value={radiusText}
        onChangeText={onCustomRadius}
        keyboardType="number-pad"
        error={errors.radius}
      />

      <Field
        label={t.capacity}
        value={capacityText}
        onChangeText={setCapacityText}
        keyboardType="number-pad"
        hint={t.capacityHint}
        error={errors.capacity}
      />

      <Toggle
        label={t.requiresApproval}
        hint={t.requiresApprovalHint}
        value={requiresApproval}
        onChange={setRequiresApproval}
      />
      {editing && <Toggle label={t.gymActive} value={isActive} onChange={setIsActive} />}

      <Banner message={message?.text ?? null} tone={message?.tone} />
      <Button title={t.saveGym} onPress={save} loading={saving} />
      {editing && user?.role === "app_admin" && (
        <ConfirmButton
          title={t.deleteGym}
          question={t.deleteGymQuestion(name)}
          confirmTitle={t.deleteGymConfirm}
          cancelTitle={t.cancel}
          onConfirm={remove}
          loading={deleting}
        />
      )}
    </Screen>
  );
}

function Toggle(props: { label: string; hint?: string; value: boolean; onChange: (v: boolean) => void }) {
  return (
    <View style={styles.toggle}>
      <View style={{ flex: 1, gap: 2 }}>
        <Text style={styles.toggleLabel}>{props.label}</Text>
        {props.hint && !props.value && <Muted>{props.hint}</Muted>}
      </View>
      <Switch
        value={props.value}
        onValueChange={props.onChange}
        trackColor={{ true: colors.primary }}
        accessibilityLabel={props.label}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  label: { fontSize: 14, fontWeight: "600", color: colors.text, marginTop: spacing.sm },
  error: { color: colors.danger, fontSize: 13 },
  note: { color: colors.muted, fontSize: 13 },
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  toggle: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    backgroundColor: colors.surface,
    padding: spacing.md,
    borderRadius: 12,
  },
  toggleLabel: { fontSize: 15, fontWeight: "500", color: colors.text },
});
