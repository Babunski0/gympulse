from tests.conftest import GYM, admin_headers, auth_headers, create_gym


def test_admin_creates_gym_with_default_radius(client):  # US-03
    admin = admin_headers(client)
    res = create_gym(client, admin)
    assert res.status_code == 201
    gym = res.json()
    assert gym["radius_m"] == 50
    assert gym["maximum_capacity"] is None
    managed = client.get("/api/v1/admin/gyms", headers=admin).json()
    assert [g["id"] for g in managed] == [gym["id"]]


def test_member_cannot_create_gym(client):
    member = auth_headers(client)
    assert create_gym(client, member).status_code == 403


def test_gym_validation_ranges(client):  # NFR-09
    admin = admin_headers(client)
    res = create_gym(client, admin, latitude=91, radius_m=10, maximum_capacity=0)
    assert res.status_code == 422
    fields = {d["field"] for d in res.json()["error"]["details"]}
    assert fields == {"latitude", "radius_m", "maximum_capacity"}


def test_admin_updates_own_gym_partially(client):  # GYM-02
    admin = admin_headers(client)
    gym_id = create_gym(client, admin, maximum_capacity=80).json()["id"]
    res = client.patch(
        f"/api/v1/gyms/{gym_id}", json={"radius_m": 120, "latitude": 42.44}, headers=admin
    )
    assert res.status_code == 200
    body = res.json()
    assert (body["radius_m"], body["latitude"], body["maximum_capacity"]) == (120, 42.44, 80)
    # Explicit null clears the optional capacity, but required fields cannot be nulled.
    cleared = client.patch(f"/api/v1/gyms/{gym_id}", json={"maximum_capacity": None}, headers=admin)
    assert cleared.json()["maximum_capacity"] is None
    bad = client.patch(f"/api/v1/gyms/{gym_id}", json={"name": None}, headers=admin)
    assert bad.status_code == 422


def test_gym_admin_cannot_change_a_gym_they_do_not_manage(client):  # TC-07, NFR-03
    app_admin = admin_headers(client)
    gym_id = create_gym(client, app_admin).json()["id"]
    other = admin_headers(client, "other@example.com", role="gym_admin")
    res = client.patch(f"/api/v1/gyms/{gym_id}", json={"radius_m": 500}, headers=other)
    assert res.status_code == 403
    assert client.get(f"/api/v1/gyms/{gym_id}", headers=app_admin).json()["radius_m"] == 50
    assert client.get(f"/api/v1/gyms/{gym_id}/memberships", headers=other).status_code == 403
    assert client.get("/api/v1/admin/gyms", headers=other).json() == []


def test_only_app_admin_creates_gyms(client):
    gym_admin = admin_headers(client, "gymadmin@example.com", role="gym_admin")
    assert create_gym(client, gym_admin).status_code == 403


def test_app_admin_sees_and_edits_every_gym(client):
    first = admin_headers(client)
    gym_id = create_gym(client, first).json()["id"]
    second = admin_headers(client, "second@example.com")
    res = client.patch(f"/api/v1/gyms/{gym_id}", json={"radius_m": 80}, headers=second)
    assert res.status_code == 200
    assert [g["id"] for g in client.get("/api/v1/admin/gyms", headers=second).json()] == [gym_id]


def test_filter_gyms_by_city(client):
    admin = admin_headers(client)
    create_gym(client, admin)
    create_gym(client, admin, name="Iron House", city="  nikšić ")
    create_gym(client, admin, name="Bar Fitness", city="Bar")
    member = auth_headers(client)
    cities = client.get("/api/v1/gyms/cities", headers=member).json()
    assert cities == ["Bar", "Nikšić", "Podgorica"]
    res = client.get("/api/v1/gyms", params={"city": "nikšić"}, headers=member).json()
    assert [g["name"] for g in res] == ["Iron House"]
    assert res[0]["city"] == "Nikšić"


def test_search_gyms(client):  # GYM-03
    admin = admin_headers(client)
    create_gym(client, admin)
    create_gym(client, admin, name="Iron House", address="Njegoševa 5", city="Nikšić")
    member = auth_headers(client)
    names = [g["name"] for g in client.get("/api/v1/gyms", headers=member).json()]
    assert names == ["Iron House", "Pulse Gym Centar"]
    found = client.get("/api/v1/gyms", params={"q": "nikšić"}, headers=member).json()
    assert [g["name"] for g in found] == ["Iron House"]


def test_inactive_gym_is_hidden_from_members(client):
    admin = admin_headers(client)
    gym_id = create_gym(client, admin).json()["id"]
    client.patch(f"/api/v1/gyms/{gym_id}", json={"is_active": False}, headers=admin)
    member = auth_headers(client)
    assert client.get("/api/v1/gyms", headers=member).json() == []
    assert client.get(f"/api/v1/gyms/{gym_id}", headers=member).status_code == 404


def test_join_open_gym_is_active_immediately(client):  # US-04
    admin = admin_headers(client)
    gym_id = create_gym(client, admin).json()["id"]
    member = auth_headers(client)
    res = client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member)
    assert res.status_code == 201
    assert res.json()["status"] == "active"
    again = client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member)
    assert again.status_code == 409
    mine = client.get("/api/v1/me/gyms", headers=member).json()
    assert mine[0]["gym"]["name"] == GYM["name"]
    assert mine[0]["membership"]["status"] == "active"


def test_join_with_approval_and_admin_decides(client):  # GYM-06
    admin = admin_headers(client)
    gym_id = create_gym(client, admin, membership_requires_approval=True).json()["id"]
    member = auth_headers(client)
    pending = client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member).json()
    assert pending["status"] == "pending"

    members = client.get(f"/api/v1/gyms/{gym_id}/memberships", headers=admin).json()
    assert [(m["email"], m["status"]) for m in members] == [("ana@example.com", "pending")]

    res = client.patch(
        f"/api/v1/gyms/{gym_id}/memberships/{pending['id']}",
        json={"status": "active"},
        headers=admin,
    )
    assert res.status_code == 200
    assert client.get("/api/v1/me/gyms", headers=member).json()[0]["membership"]["status"] == (
        "active"
    )


def test_rejected_member_can_ask_again(client):
    admin = admin_headers(client)
    gym_id = create_gym(client, admin, membership_requires_approval=True).json()["id"]
    member = auth_headers(client)
    m = client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member).json()
    client.patch(
        f"/api/v1/gyms/{gym_id}/memberships/{m['id']}", json={"status": "rejected"}, headers=admin
    )
    again = client.post(f"/api/v1/gyms/{gym_id}/memberships", headers=member)
    assert again.status_code == 201
    assert again.json()["status"] == "pending"
