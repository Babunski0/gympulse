# GymPulse – arhitektura i plan razvoja

Ovaj dokument je kratak pregled kako je GymPulse postavljen i kojim redom se gradi.
Polazna osnova su `GymPulse_Requirements_v0.1.pdf` i `GymPulse_Design_v0.1.pdf` u ovom folderu;
oni su smjernica, a odluke koje odstupaju ili ih dopunjuju zapisane su ispod.

## Arhitektura

```
mobile/ (React Native + Expo, TypeScript)
   │  HTTPS + JSON, Bearer token
   ▼
backend/ (Python, FastAPI) ── jedan servis, modularni monolit
   │  SQLAlchemy 2 + Alembic migracije
   ▼
PostgreSQL 16
```

- **Jedan backend servis** podijeljen po modulima (`auth`, `gyms`, `attendance`, `training`,
  `workouts`). Svaki modul ima svoj router (`app/api`), Pydantic šeme (`app/schemas`),
  poslovnu logiku (`app/services`) i modele (`app/models`). Poseban sloj „repositories" iz
  dizajna za sada ne uvodimo: servisi direktno koriste SQLAlchemy, što je dovoljno jasno za MVP.
- **Server odlučuje o svemu što je bitno**: GPS provjera za clock-in, prava administratora,
  jedna aktivna sesija (jedinstveni parcijalni indeks u bazi).
- **Format grešaka** je uvijek `{"error": {"code", "message", "details?"}}`, da mobilna
  aplikacija može prikazati razumljivu poruku.

## Mobilna aplikacija

- **Expo Router** (`mobile/src/app`): grupa `(auth)` sadrži prijavu i registraciju, grupa `(app)`
  ekrane za prijavljenog korisnika. Koja grupa je dostupna odlučuje `Stack.Protected` u
  `_layout.tsx`, prema tome da li je korisnik prijavljen.
- **API klijent** (`mobile/src/lib/api.ts`) dodaje token, a kad access token istekne sam ga
  osvježi jednom i ponovi zahtjev; ako ni to ne uspije, korisnik se vraća na prijavu.
- **Tokeni** se na telefonu čuvaju u Keychain/Keystore (`expo-secure-store`); u web pregledu
  (samo za razvoj) u `localStorage`.
- **Adresa servera**: `EXPO_PUBLIC_API_URL` ako je postavljen, inače računar koji pokreće
  `npx expo start`, port 8000.
- **Mapa** (`mobile/src/components/map`): `GymMap.tsx` za telefon i `GymMap.web.tsx` za pregledač,
  sa istim propsima; admin dodirom na mapu postavlja centar teretane, a krug pokazuje radijus.
- **Tekstovi** su na jednom mjestu (`mobile/src/i18n/sr.ts`), uključujući prevode kodova grešaka.

## Sigurnost (stanje nakon koraka 1)

- Lozinke: Argon2id hash.
- Prijava vraća kratkotrajni **access token** (JWT, 15 min) i **refresh token** (30 dana).
  Refresh token se u bazi čuva samo kao SHA-256 hash i rotira se pri svakom osvježavanju.
- Svaka prijava je jedan red u `auth_sessions`. Odjava ga opoziva, pa i access token te
  sesije odmah prestaje da važi (US-02: „ranija sesija više ne otvara privatne podatke").
- Ograničenje broja zahtjeva (429) na registraciju, prijavu i osvježavanje tokena.
- Van `development` okruženja API odbija da se pokrene bez pravog `GYMPULSE_JWT_SECRET`.

## Odluke za otvorena pitanja (privremene, mogu se mijenjati)

| Pitanje | Odluka za sada |
|---|---|
| Tip aplikacije | Mobilna (Android/iOS) preko Expo; admin funkcije kroz isti API |
| Članstvo u teretani | Automatski odobreno; admin po teretani može uključiti ručno odobravanje. Odbijeni korisnik može poslati novi zahtjev |
| GPS radijus | Podrazumijevano 50 m (tvoja odluka), admin mijenja po teretani (dozvoljeno 25–2000 m) |
| Preciznost GPS-a | Odbija se očitavanje lošije od 100 m ili starije od 2 min |
| Zaboravljen clock-out | Automatsko zatvaranje poslije 6 h, oznaka `auto_expired` |
| Generisanje plana | Deterministička pravila + kuriran katalog vježbi, bez AI-ja u MVP-u |
| Bučice | Upisuje se težina jedne bučice |
| Ko unosi teretane | **Admin aplikacije** (uloga `app_admin`) ručno unosi i uređuje sve teretane i njihove članove. Postaje se komandom `python -m app.cli make-admin email`. Uloga `gym_admin` (upravnik samo svoje teretane) postoji u kodu za kasnije, ali je za sada niko ne dodjeljuje |
| Gradovi | Svaka teretana ima grad; korisnici filtriraju po gradu. Naziv grada se ujednačava (`nikšić` → `Nikšić`) |
| Mape | Na telefonu `react-native-maps` (Google/Apple mape), u pregledaču Leaflet sa OpenStreetMap mapom |

## Plan po koracima

Svaki korak je zaseban, može se pregledati i pokrenuti, i ima svoje testove.
Sljedeći korak počinje tek kada prethodni odobriš.

1. ✓ **Temelj i nalozi** – struktura repoa, backend, baza i migracije, registracija, prijava,
   odjava, osvježavanje tokena, izmjena profila, Docker Compose, CI. *(AUTH-01..04)*
2. ✓ **Mobilna aplikacija: početak** – Expo projekat, ekrani za registraciju, prijavu i profil,
   povezani na API. *(US-01, US-02, US-13)*
3. ✓ **Teretane i administracija** – kreiranje i uređivanje teretane (lokacija, radijus,
   kapacitet), pretraga, učlanjenje, upravljanje članovima. *(GYM-01..04, GYM-06)*
4. **Dolazak i popunjenost** – GPS clock-in, clock-out, jedna aktivna sesija, automatsko
   zatvaranje, broj prisutnih; mobilni ekrani za mapu i check-in. *(ATT-01..06, GYM-05)*
5. **Fitness profil i plan treninga** – profil i cilj, katalog vježbi, generator plana,
   verzije plana. *(FIT-01..06)*
6. **Dnevnik treninga** – započni/završi trening, unos i ispravka serija. *(LOG-01..04)*
7. **Napredak** – grafikoni po vježbi, obim rada, lični rekordi. *(LOG-05, LOG-06)*
8. **Priprema za produkciju** – hosting, backup, retencija podataka, brisanje naloga.
