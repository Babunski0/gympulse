import { ApiError } from "@/lib/api";

/** All user-facing text in one place, so wording or a second language is a one-file change. */
export const t = {
  appName: "GymPulse",
  tagline: "Teretana, trening i napredak na jednom mjestu",
  email: "Email",
  password: "Lozinka",
  passwordHint: "Najmanje 8 znakova",
  fullName: "Ime i prezime",
  login: "Prijavi se",
  register: "Napravi nalog",
  noAccount: "Nemaš nalog? Registruj se",
  haveAccount: "Već imaš nalog? Prijavi se",
  logout: "Odjavi se",
  profile: "Profil",
  save: "Sačuvaj",
  saved: "Sačuvano",
  memberSince: "Član od",
  welcome: (name: string) => `Zdravo, ${name}!`,
  homeComingSoon:
    "Ovdje će uskoro biti check-in u teretanu, gužva, plan treninga i dnevnik. Za sada možeš urediti profil.",
  required: "Obavezno polje",
  invalidEmail: "Unesi ispravnu email adresu",
  passwordTooShort: "Lozinka mora imati najmanje 8 znakova",
};

const errorMessages: Record<string, string> = {
  network_error: "Nema veze sa serverom. Provjeri internet i da li je server pokrenut.",
  invalid_credentials: "Pogrešan email ili lozinka.",
  email_taken: "Nalog sa ovim emailom već postoji.",
  rate_limited: "Previše pokušaja. Sačekaj minut pa probaj ponovo.",
  validation_error: "Provjeri unesene podatke.",
  unauthorized: "Sesija je istekla. Prijavi se ponovo.",
};

export function errorMessage(err: unknown): string {
  if (err instanceof ApiError) return errorMessages[err.code] ?? "Došlo je do greške. Pokušaj ponovo.";
  return "Došlo je do greške. Pokušaj ponovo.";
}
