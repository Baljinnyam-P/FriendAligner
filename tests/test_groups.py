def test_add_and_remove_member(client, token_factory, group_factory, user_factory):
    token, owner = token_factory(user_factory(email="owner@test.com"))
    group, _ = group_factory(owner=owner)
    new_user = user_factory(email="new@test.com")
    headers = {"Authorization": f"Bearer {token}"}
    add_resp = client.post(f"/api/group/{group.group_id}/add_member", json={"user_id": new_user.user_id}, headers=headers)
    assert add_resp.status_code == 201
    rem_resp = client.post(f"/api/group/{group.group_id}/remove_member", json={"user_id": new_user.user_id}, headers=headers)
    assert rem_resp.status_code == 200

def test_view_members_requires_membership(client, token_factory, group_factory, user_factory):
    token, owner = token_factory(user_factory(email="owner2@test.com"))
    group, _ = group_factory(owner=owner)
    # Non-member user
    outsider_token, outsider = token_factory(user_factory(email="outsider@test.com"))
    headers = {"Authorization": f"Bearer {outsider_token}"}
    resp = client.get(f"/api/group/{group.group_id}/members", headers=headers)
    assert resp.status_code == 403
