"""Turns a typed city or street address into map coordinates.

Requests go through the backend (not straight from the app) so the provider can be swapped,
results are cached, and the provider's usage policy (identifying User-Agent, low rate) is kept.
"""

import threading
import time
from collections import OrderedDict
from typing import Literal

import httpx
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.errors import AppError

Kind = Literal["city", "address"]


class GeocodeResult(BaseModel):
    latitude: float
    longitude: float
    display_name: str


_CACHE_SIZE = 500
_STREET_RANK = 26  # Nominatim place_rank: 26+ is a street or a more precise place
_cache: OrderedDict[tuple[str, str], GeocodeResult | None] = OrderedDict()
_lock = threading.Lock()
_last_request_at = 0.0


def _fetch(query: str, kind: Kind) -> list[dict]:
    """One call to the provider. Separate function so tests can replace it."""
    global _last_request_at
    s = get_settings()
    params = {"q": query, "format": "jsonv2", "limit": 1, "accept-language": "sr-Latn,sr,en"}
    if kind == "city":
        params["featuretype"] = "settlement"
    with _lock:  # keep to roughly one request per second across the process
        wait = 1.0 - (time.monotonic() - _last_request_at)
        if wait > 0:
            time.sleep(wait)
        _last_request_at = time.monotonic()
    res = httpx.get(
        s.geocoder_url,
        params=params,
        headers={"User-Agent": s.geocoder_user_agent},
        timeout=s.geocoder_timeout_s,
    )
    res.raise_for_status()
    return res.json()


def geocode(query: str, kind: Kind) -> GeocodeResult:
    key = (kind, " ".join(query.lower().split()))
    if key in _cache:
        _cache.move_to_end(key)
        hit = _cache[key]
    else:
        try:
            rows = _fetch(query, kind)
        except (httpx.HTTPError, ValueError):
            raise AppError(
                503, "geocoding_unavailable", "Address search is unavailable right now."
            ) from None
        if kind == "address":
            # A street search that only matched the town would drop the pin in the town centre.
            rows = [r for r in rows if int(r.get("place_rank", 30)) >= _STREET_RANK]
        hit = (
            GeocodeResult(
                latitude=float(rows[0]["lat"]),
                longitude=float(rows[0]["lon"]),
                display_name=rows[0].get("display_name", query),
            )
            if rows
            else None
        )
        _cache[key] = hit
        if len(_cache) > _CACHE_SIZE:
            _cache.popitem(last=False)
    if hit is None:
        raise AppError(404, "location_not_found", "No place found for this search.")
    return hit


def clear_cache() -> None:
    _cache.clear()
