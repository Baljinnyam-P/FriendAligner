def test_register_and_login(client):
    r = client.post("/api/auth/register", json={"email": "a@test.com", "password": "pass"})
    assert r.status_code == 201
    r2 = client.post("/api/auth/login", json={"email": "a@test.com", "password": "pass"})
    assert r2.status_code == 200
    assert "access_token" in r2.get_json()
