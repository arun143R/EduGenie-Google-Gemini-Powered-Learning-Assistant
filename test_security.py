from fastapi.testclient import TestClient


class TestSecurity:
    def test_cookie_has_httponly_flag(self, client: TestClient):
        client.post("/api/auth/register", json={
            "username": "secuser",
            "email": "sec@example.com",
            "password": "testpass123"
        })
        response = client.post("/api/auth/login", data={
            "username": "secuser",
            "password": "testpass123"
        })
        cookie_header = response.headers.get("set-cookie", "")
        assert "httponly" in cookie_header.lower()

    def test_cookie_has_samesite_lax(self, client: TestClient):
        client.post("/api/auth/register", json={
            "username": "secuser2",
            "email": "sec2@example.com",
            "password": "testpass123"
        })
        response = client.post("/api/auth/login", data={
            "username": "secuser2",
            "password": "testpass123"
        })
        cookie_header = response.headers.get("set-cookie", "")
        assert "samesite=lax" in cookie_header.lower()

    def test_cookie_has_secure_flag(self, client: TestClient):
        client.post("/api/auth/register", json={
            "username": "secuser3",
            "email": "sec3@example.com",
            "password": "testpass123"
        })
        response = client.post("/api/auth/login", data={
            "username": "secuser3",
            "password": "testpass123"
        })
        cookie_header = response.headers.get("set-cookie", "")
        assert "secure" in cookie_header.lower()

    def test_csrf_rejects_wrong_origin(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/qna/ask",
            json={"question": "What is Python?"},
            headers={**auth_headers, "origin": "https://evil-site.com"}
        )
        assert response.status_code == 403
        assert "csrf" in response.json()["detail"].lower()

    def test_csrf_allows_same_origin(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/qna/ask",
            json={"question": "What is Python?"},
            headers={**auth_headers, "origin": "http://testserver"}
        )
        assert response.status_code != 403

    def test_csrf_rejects_wrong_referer(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/qna/ask",
            json={"question": "What is Python?"},
            headers={**auth_headers, "referer": "https://evil-site.com/attack"}
        )
        assert response.status_code == 403
        assert "csrf" in response.json()["detail"].lower()

    def test_csrf_allows_no_origin(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/qna/ask",
            json={"question": "What is Python?"},
            headers=auth_headers
        )
        assert response.status_code != 403

    def test_history_response_no_user_id(self, client: TestClient, auth_headers):
        response = client.get("/api/history/list", headers=auth_headers)
        assert response.status_code == 200
        if len(response.json()) > 0:
            assert "user_id" not in response.json()[0]
