from fastapi.testclient import TestClient


class TestInputValidation:
    def test_register_short_username(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "ab",
            "email": "ab@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 422

    def test_register_short_password(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "validuser",
            "email": "valid@example.com",
            "password": "12345"
        })
        assert response.status_code == 422

    def test_register_invalid_email(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "validuser",
            "email": "notanemail",
            "password": "testpass123"
        })
        assert response.status_code == 422

    def test_register_empty_username(self, client: TestClient):
        response = client.post("/api/auth/register", json={
            "username": "",
            "email": "valid@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 422

    def test_qna_empty_question(self, client: TestClient, auth_headers):
        response = client.post("/api/qna/ask", headers=auth_headers, json={
            "question": ""
        })
        assert response.status_code == 422
        assert "question" in response.json()["detail"][0]["loc"]

    def test_qna_whitespace_question(self, client: TestClient, auth_headers):
        response = client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "   "
        })
        assert response.status_code == 400

    def test_explain_empty_concept(self, client: TestClient, auth_headers):
        response = client.post("/api/explanation/explain", headers=auth_headers, json={
            "concept": "",
            "level": "beginner"
        })
        assert response.status_code == 422

    def test_quiz_num_questions_below_min(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Python",
            "num_questions": 1
        })
        assert response.status_code == 422

    def test_quiz_num_questions_above_max(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Python",
            "num_questions": 100
        })
        assert response.status_code == 422

    def test_quiz_num_questions_valid_boundary(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Python",
            "num_questions": 3
        })
        assert response.status_code == 200

    def test_quiz_num_questions_valid_upper_boundary(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Python",
            "num_questions": 15
        })
        assert response.status_code == 200

    def test_roadmap_empty_topic(self, client: TestClient, auth_headers):
        response = client.post("/api/roadmap/generate", headers=auth_headers, json={
            "topic": ""
        })
        assert response.status_code == 422

    def test_quiz_empty_topic(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": ""
        })
        assert response.status_code == 422

    def test_summary_empty_text(self, client: TestClient, auth_headers):
        response = client.post("/api/summary/summarize", headers=auth_headers, json={
            "text": "",
            "length": "medium"
        })
        assert response.status_code == 422

    def test_explain_invalid_level(self, client: TestClient, auth_headers):
        response = client.post("/api/explanation/explain", headers=auth_headers, json={
            "concept": "Python",
            "level": "expert"
        })
        assert response.status_code == 422
        assert "level" in response.json()["detail"][0]["loc"]

    def test_summary_invalid_length(self, client: TestClient, auth_headers):
        response = client.post("/api/summary/summarize", headers=auth_headers, json={
            "text": "Some text here",
            "length": "xlong"
        })
        assert response.status_code == 422
        assert "length" in response.json()["detail"][0]["loc"]
