import { Stack, router, useLocalSearchParams } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Switch, Text, View } from "react-native";

import { GymMap } from "@/components/map/GymMap";
import type { Coords } from "@/components/map/types";
import { Banner, Button, Chip, Field, Muted, Screen } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, ApiError, type GymInput } from "@/lib/api";
import { getCurrentLocation } from "@/lib/location";

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
      <Field label={t.city} value={city} onChangeText={setCity} error={errors.city} placeholder="npr. Podgorica" />
      <Field label={t.address} value={address} onChangeText={setAddress} error={errors.address} />

      <Text style={styles.label}>{t.location}</Text>
      <Muted>{t.locationHint}</Muted>
      <GymMap
        value={coords}
        radiusM={radius >= 25 && radius <= 2000 ? radius : DEFAULT_RADIUS}
        height={320}
        onChange={(c) => {
          setCoords(c);
          setErrors((e) => ({ ...e, location: undefined }));
        }}
      />
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
