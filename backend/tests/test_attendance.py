from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

from sqlalchemy import func, select, update

from app.core.db import SessionLocal
from app.models import AttendanceSession
from app.models._base import utcnow
from tests.conftest import GYM, admin_headers, auth_headers, create_gym

# About 30 m and 70 m north of the test gym (one degree of latitude is ~111 km).
NEAR = {"latitude": GYM["latitude"] + 0.00027, "longitude": GYM["longitude"]}
EDGE = {"latitude": GYM["latitude"] + 0.00063, "longitude": GYM["longitude"]}
FAR = {"latitude": GYM["latitude"] + 0.01, "longitude": GYM["longitude"]}


def gym_with_member(client, email="ana@example.com", **gym):
    admin = admin_headers(client)
    gym_id = create_gym(client, admin, **gym).json()["id"]
    member = auth_headers(client, email)
    assert client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member).status_code == 201
    return admin, gym_id, member


def check_in(client, headers, gym_id, where=NEAR, accuracy_m=10):
    return client.post(
        "/api/v1/attendance/check-in",
        json={"gym_id": gym_id, **where, "accuracy_m": accuracy_m},
        headers=headers,
    )


def occupancy(client, headers, gym_id):
    return client.get(f"/api/v1/gyms/{gym_id}/occupancy", headers=headers).json()


def open_sessions() -> int:
    with SessionLocal() as db:
        return db.scalar(select(func.count()).where(AttendanceSession.check_out_at.is_(None)))


def test_check_in_inside_radius_opens_one_session(client):  # TC-01
    _, gym_id, member = gym_with_member(client)
    res = check_in(client, member, gym_id)
    assert res.status_code == 201
    body = res.json()
    assert body["gym_name"] == GYM["name"]
    assert body["check_out_at"] is None
    assert body["duration_minutes"] == 0
    current = client.get("/api/v1/attendance/current", headers=member).json()["session"]
    assert current["id"] == body["id"]


def test_check_in_outside_radius_is_rejected(client):  # TC-02
    _, gym_id, member = gym_with_member(client)
    res = check_in(client, member, gym_id, where=FAR)
    assert res.status_code == 403
    error = res.json()["error"]
    assert error["code"] == "outside_gym_radius"
    assert error["details"]["radius_m"] == 50
    assert 1000 < error["details"]["distance_m"] < 1200
    assert open_sessions() == 0


def test_gps_error_is_forgiven_only_up_to_the_allowance(client):
    _, gym_id, member = gym_with_member(client)
    # 70 m away from a 50 m gym: fine with a 25 m GPS error, not with a precise 5 m fix.
    assert check_in(client, member, gym_id, where=EDGE, accuracy_m=5).status_code == 403
    assert check_in(client, member, gym_id, where=EDGE, accuracy_m=25).status_code == 201


def test_inaccurate_location_is_rejected(client):  # TC-03
    _, gym_id, member = gym_with_member(client)
    res = check_in(client, member, gym_id, accuracy_m=250)
    assert res.status_code == 422
    assert res.json()["error"]["code"] == "location_inaccurate"
    assert open_sessions() == 0


def test_check_in_requires_active_membership(client):
    admin, gym_id, _ = gym_with_member(client, membership_requires_approval=True)
    stranger = auth_headers(client, "marko@example.com")
    assert check_in(client, stranger, gym_id).status_code == 403
    # Ana's request is still pending approval.
    pending = auth_headers(client, "ana@example.com")
    assert check_in(client, pending, gym_id).status_code == 403


def test_second_check_in_is_rejected(client):
    _, gym_id, member = gym_with_member(client)
    assert check_in(client, member, gym_id).status_code == 201
    res = check_in(client, member, gym_id)
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "already_checked_in"


def test_parallel_check_ins_open_exactly_one_session(client):  # TC-04
    _, gym_id, member = gym_with_member(client)
    with ThreadPoolExecutor(max_workers=6) as pool:
        codes = list(pool.map(lambda _: check_in(client, member, gym_id).status_code, range(6)))
    assert sorted(codes) == [201] + [409] * 5
    assert open_sessions() == 1


def test_check_out_works_from_anywhere(client):  # TC-05
    _, gym_id, member = gym_with_member(client)
    check_in(client, member, gym_id)
    res = client.post("/api/v1/attendance/check-out", headers=member)
    assert res.status_code == 200
    body = res.json()
    assert body["check_out_at"] is not None
    assert body["close_reason"] == "user"
    assert client.get("/api/v1/attendance/current", headers=member).json()["session"] is None
    again = client.post("/api/v1/attendance/check-out", headers=member)
    assert again.status_code == 409


def test_occupancy_follows_check_ins_and_outs(client):  # TC-06
    admin, gym_id, ana = gym_with_member(client, maximum_capacity=4)
    marko = auth_headers(client, "marko@example.com")
    client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=marko)
    assert occupancy(client, ana, gym_id) == {
        "current": 0,
        "maximum_capacity": 4,
        "percent": 0,
        "level": "low",
    }
    check_in(client, ana, gym_id)
    check_in(client, marko, gym_id)
    assert occupancy(client, ana, gym_id)["current"] == 2
    assert occupancy(client, ana, gym_id)["level"] == "medium"
    client.post("/api/v1/attendance/check-out", headers=marko)
    assert occupancy(client, ana, gym_id)["percent"] == 25
    # Lists carry the same number, for members and for the admin.
    listed = client.get("/api/v1/gyms", headers=ana).json()[0]
    assert listed["occupancy"]["current"] == 1
    managed = client.get("/api/v1/admin/gyms", headers=admin).json()[0]
    assert managed["occupancy"]["current"] == 1


def test_occupancy_without_capacity_has_no_percentage(client):  # US-07
    _, gym_id, member = gym_with_member(client)
    check_in(client, member, gym_id)
    assert occupancy(client, member, gym_id) == {
        "current": 1,
        "maximum_capacity": None,
        "percent": None,
        "level": None,
    }


def test_forgotten_session_is_closed_automatically(client):  # TC-10
    _, gym_id, member = gym_with_member(client)
    check_in(client, member, gym_id)
    started = utcnow() - timedelta(hours=7)
    with SessionLocal() as db:
        db.execute(update(AttendanceSession).values(check_in_at=started))
        db.commit()
    assert occupancy(client, member, gym_id)["current"] == 0
    assert client.get("/api/v1/attendance/current", headers=member).json()["session"] is None
    with SessionLocal() as db:
        session = db.scalar(select(AttendanceSession))
        assert session.close_reason == "auto_expired"
        assert session.check_out_at == started + timedelta(hours=6)
    # The member can check in again right away.
    assert check_in(client, member, gym_id).status_code == 201
