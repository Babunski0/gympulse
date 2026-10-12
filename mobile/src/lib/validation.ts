import { t } from "@/i18n/sr";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

export type FieldErrors = Partial<Record<"email" | "password" | "full_name", string>>;

/** Quick client-side checks; the server validates again and has the final say. */
export function validateCredentials(email: string, password: string, fullName?: string): FieldErrors {
  const errors: FieldErrors = {};
  if (!email.trim()) errors.email = t.required;
  else if (!EMAIL_RE.test(email.trim())) errors.email = t.invalidEmail;
  if (!password) errors.password = t.required;
  else if (fullName !== undefined && password.length < 8) errors.password = t.passwordTooShort;
  if (fullName !== undefined && !fullName.trim()) errors.full_name = t.required;
  return errors;
}
