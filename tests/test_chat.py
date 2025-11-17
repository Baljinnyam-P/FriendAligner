def test_chat_post_and_list(client, token_factory, group_factory, member_factory, user_factory):
    group, owner = group_factory()
    # add member
    _, member_user = member_factory(group)
    member_token, _ = token_factory(member_user)
    headers = {"Authorization": f"Bearer {member_token}"}
    post_resp = client.post(f"/api/chat/{group.group_id}/message", json={"content": "Hello group"}, headers=headers)
    assert post_resp.status_code == 201
    list_resp = client.get(f"/api/chat/{group.group_id}/messages", headers=headers)
    assert list_resp.status_code == 200
    msgs = list_resp.get_json()
    assert any(m["content"] == "Hello group" for m in msgs)
