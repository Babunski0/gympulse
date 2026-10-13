import os

os.environ.setdefault(
    "GYMPULSE_DATABASE_URL", "postgresql+psycopg://postgres:postgres@localhost:5432/gympulse_test"
)
os.environ.setdefault("GYMPULSE_JWT_SECRET", "test-secret-that-is-long-enough-for-hs256")

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.core.db import Base, engine  # noqa: E402
from app.core.rate_limit import limiter  # noqa: E402
from app.main import app  # noqa: E402

BACKEND_DIR = os.path.dirname(os.path.dirname(__file__))


@pytest.fixture(scope="session", autouse=True)
def _migrated_db():
    with engine.begin() as conn:
        conn.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    command.upgrade(cfg, "head")
    yield


@pytest.fixture(autouse=True)
def _clean_tables():
    yield
    tables = ", ".join(t.name for t in Base.metadata.sorted_tables)
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {tables} CASCADE"))
    limiter.reset()


@pytest.fixture
def client() -> TestClient:
    return TestClient(app)


def register(
    client: TestClient,
    email: str = "ana@example.com",
    password: str = "lozinka123",
    full_name: str = "Ana Anić",
):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": full_name},
    )


def login(client: TestClient, email: str = "ana@example.com", password: str = "lozinka123"):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def auth_headers(client: TestClient, email: str = "ana@example.com") -> dict[str, str]:
    register(client, email=email)
    token = login(client, email=email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_admin(email: str, role: str = "app_admin") -> None:
    from sqlalchemy import update

    from app.core.db import SessionLocal
    from app.models import User

    with SessionLocal() as db:
        db.execute(update(User).where(User.email == email).values(role=role))
        db.commit()


def admin_headers(
    client: TestClient, email: str = "admin@example.com", role: str = "app_admin"
) -> dict[str, str]:
    register(client, email=email)
    make_admin(email, role)
    token = login(client, email=email).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


GYM = {
    "name": "Pulse Gym Centar",
    "address": "Bulevar Svetog Petra Cetinjskog 1",
    "city": "Podgorica",
    "latitude": 42.4411,
    "longitude": 19.2627,
}


def create_gym(client: TestClient, headers: dict[str, str], **overrides):
    return client.post("/api/v1/gyms", json={**GYM, **overrides}, headers=headers)
