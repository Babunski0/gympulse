import { router } from "expo-router";
import { useEffect, useState } from "react";
import { StyleSheet, Text, View } from "react-native";

import { Banner, Button, Chip, Field, Muted, Screen, SectionTitle } from "@/components/ui";
import { colors, spacing } from "@/components/theme";
import { errorMessage, t } from "@/i18n/sr";
import { api, type EquipmentAccess, type Experience, type Goal } from "@/lib/api";

const GOALS: Goal[] = ["muscle", "strength", "fat_loss", "endurance", "general"];
const EXPERIENCES: Experience[] = ["beginner", "intermediate", "advanced"];
const EQUIPMENTS: EquipmentAccess[] = ["gym", "dumbbells", "bodyweight"];
const DAYS = [2, 3, 4, 5, 6];
const MINUTES = [30, 45, 60, 75, 90];

/** Empty text is fine (the field is optional); anything else must be a number in range. */
function parseOptional(text: string, min: number, max: number): number | null | "invalid" {
  const clean = text.trim().replace(",", ".");
  if (!clean) return null;
  const n = Number(clean);
  return Number.isFinite(n) && n >= min && n <= max ? n : "invalid";
}

export default function FitnessProfileScreen() {
  const [goal, setGoal] = useState<Goal | null>(null);
  const [experience, setExperience] = useState<Experience | null>(null);
  const [equipment, setEquipment] = useState<EquipmentAccess>("gym");
  const [days, setDays] = useState(3);
  const [minutes, setMinutes] = useState(60);
  const [birthYear, setBirthYear] = useState("");
  const [height, setHeight] = useState("");
  const [weight, setWeight] = useState("");
  const [hadProfile, setHadProfile] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [message, setMessage] = useState<{ text: string; tone: "error" | "success" } | null>(null);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    api
      .getFitness()
      .then((p) => {
        if (!p) return;
        setHadProfile(true);
        setGoal(p.training_goal);
        setExperience(p.experience_level);
        setEquipment(p.equipment);
        setDays(p.days_per_week);
        setMinutes(p.session_minutes);
        setBirthYear(p.birth_year ? String(p.birth_year) : "");
        setHeight(p.height_cm ? String(p.height_cm) : "");
        setWeight(p.weight_kg ? String(p.weight_kg).replace(".", ",") : "");
      })
      .catch((err) => setMessage({ text: errorMessage(err), tone: "error" }));
  }, []);

  async function save() {
    setMessage(null);
    const thisYear = new Date().getFullYear();
    const birth = parseOptional(birthYear, 1920, thisYear - 12);
    const h = parseOptional(height, 100, 250);
    const w = parseOptional(weight, 30, 300);
    const next: Record<string, string> = {};
    if (!goal) next.goal = t.pickOne;
    if (!experience) next.experience = t.pickOne;
    if (birth === "invalid") next.birthYear = t.invalidNumber;
    if (h === "invalid") next.height = t.invalidNumber;
    if (w === "invalid") next.weight = t.invalidNumber;
    setErrors(next);
    if (Object.keys(next).length || !goal || !experience) return;

    setSaving(true);
    try {
      await api.saveFitness({
        training_goal: goal,
        experience_level: experience,
        equipment,
        days_per_week: days,
        session_minutes: minutes,
        birth_year: birth as number | null,
        height_cm: h === null ? null : Math.round(h as number),
        weight_kg: w as number | null,
      });
      setMessage({ text: hadProfile ? t.profileChangedHint : t.profileSaved, tone: "success" });
      setSaved(true);
    } catch (err) {
      setMessage({ text: errorMessage(err), tone: "error" });
    } finally {
      setSaving(false);
    }
  }

  return (
    <Screen>
      <Muted>{t.fitnessIntro}</Muted>

      <SectionTitle>{t.goal}</SectionTitle>
      <Choices
        options={GOALS}
        value={goal}
        labels={t.goals}
        onChange={(g) => {
          setGoal(g);
          setErrors(({ goal: _, ...rest }) => rest);
        }}
        error={errors.goal}
      />

      <SectionTitle>{t.experience}</SectionTitle>
      <Choices
        options={EXPERIENCES}
        value={experience}
        labels={t.experiences}
        onChange={(e) => {
          setExperience(e);
          setErrors(({ experience: _, ...rest }) => rest);
        }}
        error={errors.experience}
      />
      <Muted>{t.experienceHint}</Muted>

      <SectionTitle>{t.equipmentLabel}</SectionTitle>
      <Choices options={EQUIPMENTS} value={equipment} labels={t.equipments} onChange={setEquipment} />

      <SectionTitle>{t.daysPerWeek}</SectionTitle>
      <Choices
        options={DAYS}
        value={days}
        labels={Object.fromEntries(DAYS.map((d) => [d, t.daysValue(d)]))}
        onChange={setDays}
      />

      <SectionTitle>{t.sessionMinutes}</SectionTitle>
      <Choices
        options={MINUTES}
        value={minutes}
        labels={Object.fromEntries(MINUTES.map((m) => [m, t.minutesValue(m)]))}
        onChange={setMinutes}
      />

      <SectionTitle>{t.bodyOptional}</SectionTitle>
      <View style={styles.row}>
        <View style={styles.cell}>
          <Field
            label={t.heightCm}
            value={height}
            onChangeText={setHeight}
            keyboardType="number-pad"
            error={errors.height}
          />
        </View>
        <View style={styles.cell}>
          <Field
            label={t.weightKg}
            value={weight}
            onChangeText={setWeight}
            keyboardType="decimal-pad"
            error={errors.weight}
          />
        </View>
      </View>
      <Field
        label={t.birthYear}
        value={birthYear}
        onChangeText={setBirthYear}
        keyboardType="number-pad"
        placeholder="npr. 1998"
        error={errors.birthYear}
      />

      <Banner message={message?.text ?? null} tone={message?.tone} />
      <Button title={t.saveProfile} onPress={save} loading={saving} variant={saved ? "ghost" : "primary"} />
      {saved && <Button title={t.goToPlan} onPress={() => router.replace("/plan")} />}
    </Screen>
  );
}

function Choices<T extends string | number>(props: {
  options: T[];
  value: T | null;
  labels: Record<string, string>;
  onChange: (value: T) => void;
  error?: string;
}) {
  return (
    <View style={{ gap: spacing.xs }}>
      <View style={styles.chips}>
        {props.options.map((option) => (
          <Chip
            key={String(option)}
            label={props.labels[String(option)]}
            selected={props.value === option}
            onPress={() => props.onChange(option)}
          />
        ))}
      </View>
      {props.error && <Text style={styles.error}>{props.error}</Text>}
    </View>
  );
}

const styles = StyleSheet.create({
  chips: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  error: { color: colors.danger, fontSize: 13 },
  row: { flexDirection: "row", gap: spacing.sm },
  cell: { flex: 1 },
});
