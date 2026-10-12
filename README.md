# GymPulse

Mobilna aplikacija za evidenciju dolazaka u teretanu (GPS check-in), prikaz gužve,
personalizovane planove treninga i praćenje napretka.

- Arhitektura i plan po koracima: [docs/ARHITEKTURA.md](docs/ARHITEKTURA.md)
- Zahtjevi i dizajn: [docs/](docs/)

## Struktura

```
backend/   Python + FastAPI API, Alembic migracije, testovi
mobile/    React Native + Expo aplikacija (od koraka 2)
infra/     Docker Compose i primjer konfiguracije
docs/      Dokumentacija
```

## Pokretanje backenda

### Najlakše: Docker

Potreban je [Docker Desktop](https://www.docker.com/products/docker-desktop/).

```powershell
cd infra
copy .env.example .env      # na macOS/Linux: cp .env.example .env
docker compose up --build
```

API je na http://localhost:8000, a interaktivna dokumentacija na http://localhost:8000/docs.

### Bez Dockera (za razvoj)

Potrebni su Python 3.12+ i PostgreSQL 16 (može i samo baza iz Dockera:
`docker compose -f infra/docker-compose.yml up db`).

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate          # na macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
copy .env.example .env          # pa upiši svoje vrijednosti
alembic upgrade head
uvicorn app.main:app --reload
```

### Testovi

Testovi koriste posebnu bazu `gympulse_test` (napravi je jednom: `createdb gympulse_test`,
ili u Dockeru `docker compose -f infra/docker-compose.yml exec db createdb -U gympulse gympulse_test`).

```powershell
cd backend
$env:GYMPULSE_DATABASE_URL="postgresql+psycopg://gympulse:gympulse@localhost:5432/gympulse_test"
pytest
ruff check .
```

## API (korak 1)

| Metoda | Putanja | Opis |
|---|---|---|
| POST | `/api/v1/auth/register` | Novi nalog (email, lozinka min. 8 znakova, ime) |
| POST | `/api/v1/auth/login` | Prijava, vraća access i refresh token |
| POST | `/api/v1/auth/refresh` | Novi par tokena (stari refresh token prestaje da važi) |
| POST | `/api/v1/auth/logout` | Odjava ove sesije |
| GET | `/api/v1/me` | Moj nalog |
| PUT | `/api/v1/me` | Izmjena imena |
| GET | `/health` | Provjera da API radi |
