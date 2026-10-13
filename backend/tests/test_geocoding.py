import httpx
import pytest

from app.services import geocoding
from tests.conftest import admin_headers, auth_headers

PODGORICA = [
    {"lat": "42.4304", "lon": "19.2594", "display_name": "Podgorica, Crna Gora", "place_rank": 16}
]
STREET = [
    {"lat": "42.4378", "lon": "19.2481", "display_name": "Bulevar, Podgorica", "place_rank": 26}
]


@pytest.fixture
def fake_provider(monkeypatch):
    calls = []

    def fetch(query, kind):
        calls.append((query, kind))
        if query == "down":
            raise httpx.ConnectError("offline")
        if "bulevar" in query.lower():
            return STREET
        return PODGORICA if "podgorica" in query.lower() else []

    monkeypatch.setattr(geocoding, "_fetch", fetch)
    geocoding.clear_cache()
    yield calls
    geocoding.clear_cache()


def test_admin_finds_city_and_result_is_cached(client, fake_provider):
    admin = admin_headers(client)
    for _ in range(2):
        res = client.get(
            "/api/v1/geocode", params={"q": "Podgorica", "kind": "city"}, headers=admin
        )
        assert res.status_code == 200
        assert res.json() == {
            "latitude": 42.4304,
            "longitude": 19.2594,
            "display_name": "Podgorica, Crna Gora",
        }
    assert fake_provider == [("Podgorica", "city")]


def test_unknown_place_and_provider_down(client, fake_provider):
    admin = admin_headers(client)
    missing = client.get("/api/v1/geocode", params={"q": "Nepostojeće"}, headers=admin)
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "location_not_found"
    down = client.get("/api/v1/geocode", params={"q": "down"}, headers=admin)
    assert down.status_code == 503


def test_members_cannot_use_geocoding(client, fake_provider):
    member = auth_headers(client)
    assert (
        client.get("/api/v1/geocode", params={"q": "Podgorica"}, headers=member).status_code == 403
    )


def test_address_search_ignores_town_only_matches(client, fake_provider):
    admin = admin_headers(client)
    street = client.get("/api/v1/geocode", params={"q": "Bulevar 10, Podgorica"}, headers=admin)
    assert street.json()["latitude"] == 42.4378
    # Unknown street: the provider only matches the town, which must not count as the address.
    unknown = client.get(
        "/api/v1/geocode", params={"q": "Nepostojeća 99, Podgorica"}, headers=admin
    )
    assert unknown.status_code == 404
