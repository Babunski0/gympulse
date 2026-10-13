# GymPulse

Mobilna aplikacija za evidenciju dolazaka u teretanu (GPS check-in), prikaz gužve,
personalizovane planove treninga i praćenje napretka.

- Arhitektura i plan po koracima: [docs/ARHITEKTURA.md](docs/ARHITEKTURA.md)
- Zahtjevi i dizajn: [docs/](docs/)

## Struktura

```
backend/   Python + FastAPI API, Alembic migracije, testovi
mobile/    React Native + Expo aplikacija (Expo Router, TypeScript)
infra/     Docker Compose i primjer konfiguracije
docs/      Dokumentacija
```

## Pokretanje na Windowsu (bez Dockera)

Potrebno je instalirati jednom:
- [Python 3.12+](https://www.python.org/downloads/) (pri instalaciji označi „Add Python to PATH")
- [PostgreSQL 16](https://www.postgresql.org/download/windows/) (zapamti lozinku koju postaviš za korisnika `postgres`)
- [Node.js LTS](https://nodejs.org/)
- Na telefonu aplikaciju **Expo Go** (Google Play / App Store)

### 1. Baza

Otvori **pgAdmin** (dolazi uz PostgreSQL) i napravi bazu `gympulse`
(desni klik na *Databases* → *Create* → *Database*). Za testove napravi i `gympulse_test`.

### 2. Backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements-dev.txt
copy .env.example .env
```

U `backend\.env` upiši svoju lozinku za bazu:
`GYMPULSE_DATABASE_URL=postgresql+psycopg://postgres:TVOJA_LOZINKA@localhost:5432/gympulse`

```powershell
alembic upgrade head
uvicorn app.main:app --reload --host 0.0.0.0
```

API sada radi na http://localhost:8000, a dokumentacija je na http://localhost:8000/docs.
Ako Windows pita da li da dozvoli Pythonu pristup mreži, dozvoli za privatne mreže
(bez toga telefon ne može da dođe do servera).

### 3. Mobilna aplikacija

U novom terminalu (backend neka radi):

```powershell
cd mobile
npm install
npx expo start
```

Skeniraj QR kod iz terminala aplikacijom Expo Go (telefon i računar moraju biti na istoj
Wi-Fi mreži). Aplikacija sama pronalazi server na računaru koji je pokrenuo `expo start`.
Za brzi pregled u pregledaču pritisni `w` u terminalu.

### Kako postati administrator teretane

Registruj se u aplikaciji, pa u terminalu backenda (sa aktiviranim `.venv`) pokreni:

```powershell
python -m app.cli make-admin tvoj@email.com
```

Odjavi se i ponovo prijavi: na početnom ekranu pojaviće se dugme **Administracija**.

### Testovi

```powershell
cd backend
$env:GYMPULSE_DATABASE_URL="postgresql+psycopg://postgres:TVOJA_LOZINKA@localhost:5432/gympulse_test"
pytest
ruff check .

cd ..\mobile
npm run typecheck
```

## Pokretanje uz Docker (opciono)

Ako kasnije instaliraš Docker Desktop, backend i baza se mogu pokrenuti jednom komandom:

```powershell
cd infra
copy .env.example .env
docker compose up --build
```

## API

| Metoda | Putanja | Opis |
|---|---|---|
| POST | `/api/v1/auth/register` | Novi nalog (email, lozinka min. 8 znakova, ime) |
| POST | `/api/v1/auth/login` | Prijava, vraća access i refresh token |
| POST | `/api/v1/auth/refresh` | Novi par tokena (stari refresh token prestaje da važi) |
| POST | `/api/v1/auth/logout` | Odjava ove sesije |
| GET | `/api/v1/me` | Moj nalog |
| PUT | `/api/v1/me` | Izmjena imena |
| GET | `/api/v1/gyms?q=` | Lista i pretraga teretana |
| GET | `/api/v1/gyms/{id}` | Detalji teretane |
| POST | `/api/v1/gyms` | Admin: nova teretana (radijus podrazumijevano 50 m) |
| PATCH | `/api/v1/gyms/{id}` | Admin: izmjena svoje teretane |
| POST | `/api/v1/gyms/{id}/memberships` | Učlanjenje ili zahtjev za članstvo |
| GET | `/api/v1/gyms/{id}/memberships` | Admin: članovi teretane |
| PATCH | `/api/v1/gyms/{id}/memberships/{membershipId}` | Admin: odobri/odbij člana |
| GET | `/api/v1/me/gyms` | Moje teretane i status članstva |
| GET | `/api/v1/admin/gyms` | Admin: teretane kojima upravljam |
| GET | `/health` | Provjera da API radi |
