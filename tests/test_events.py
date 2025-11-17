from datetime import date

def test_create_event(client, token_factory, group_factory, member_factory, user_factory):
    group, owner = group_factory()
    token, _ = token_factory(owner)
    headers = {"Authorization": f"Bearer {token}"}
    resp = client.post("/api/events/create", json={"group_id": group.group_id, "name": "Brunch", "date": date.today().strftime("%Y-%m-%d")}, headers=headers)
    assert resp.status_code == 201
    event_id = resp.get_json()["event_id"]
    list_resp = client.get(f"/api/events/group/{group.group_id}", headers=headers)
    assert list_resp.status_code == 200
    assert any(e["event_id"] == event_id for e in list_resp.get_json())

def test_finalize_requires_organizer(client, token_factory, group_factory, member_factory, user_factory):
    group, owner = group_factory()
    # create event as owner
    owner_token, _ = token_factory(owner)
    headers_owner = {"Authorization": f"Bearer {owner_token}"}
    create_resp = client.post("/api/events/create", json={"group_id": group.group_id, "name": "Dinner", "date": date.today().strftime("%Y-%m-%d")}, headers=headers_owner)
    event_id = create_resp.get_json()["event_id"]
    # outsider member (non-organizer)
    member_gm, member_user = member_factory(group)
    member_token, _ = token_factory(member_user)
    headers_member = {"Authorization": f"Bearer {member_token}"}
    # finalize attempt by member should fail 403
    fin_fail = client.post(f"/api/events/finalize/{event_id}", headers=headers_member)
    assert fin_fail.status_code == 403
    # finalize by organizer succeeds
    fin_ok = client.post(f"/api/events/finalize/{event_id}", headers=headers_owner)
    assert fin_ok.status_code == 200
