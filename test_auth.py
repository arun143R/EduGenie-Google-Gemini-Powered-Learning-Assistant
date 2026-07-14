from fastapi.testclient import TestClient


class TestAuth:
    def test_register_success(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data
        assert "hashed_password" not in data

    def test_register_duplicate_username(self, client: TestClient, registered_user):
        response = client.post("/api/auth/register", json={
            "username": "existinguser",
            "email": "other@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    def test_register_duplicate_email(self, client: TestClient, registered_user):
        response = client.post("/api/auth/register", json={
            "username": "anotheruser",
            "email": "existing@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 409
        assert "already registered" in response.json()["detail"].lower()

    def test_login_success(self, client: TestClient, registered_user):
        response = client.post("/api/auth/login", data={
            "username": "existinguser",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert "access_token" in response.cookies

    def test_login_wrong_password(self, client: TestClient, registered_user):
        response = client.post("/api/auth/login", data={
            "username": "existinguser",
            "password": "wrongpassword"
        })
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        response = client.post("/api/auth/login", data={
            "username": "nobody",
            "password": "somepass"
        })
        assert response.status_code == 401

    def test_logout(self, client: TestClient, auth_cookies):
        response = client.post("/api/auth/logout", cookies=auth_cookies)
        assert response.status_code == 200
        assert response.json()["message"] == "Logged out successfully."

    def test_access_protected_route_without_auth(self, client: TestClient):
        response = client.get("/api/history/list")
        assert response.status_code == 401

    def test_access_protected_route_with_token(self, client: TestClient, auth_headers):
        response = client.get("/api/history/list", headers=auth_headers)
        assert response.status_code == 200
