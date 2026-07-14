from fastapi.testclient import TestClient


class TestQuiz:
    def test_generate_quiz_success(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "World History",
            "num_questions": 5
        })
        assert response.status_code == 200
        data = response.json()
        assert "quiz_id" in data
        assert data["topic"] == "World History"
        assert len(data["questions"]) == 5

    def test_generate_quiz_has_correct_structure(self, client: TestClient, auth_headers):
        response = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Algebra",
            "num_questions": 3
        })
        data = response.json()
        for q in data["questions"]:
            assert "id" in q
            assert "question_text" in q
            assert "options" in q
            assert len(q["options"]) == 4
            for opt in q["options"]:
                assert "label" in opt
                assert "text" in opt

    def test_submit_quiz_success(self, client: TestClient, auth_headers):
        gen = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Biology",
            "num_questions": 3
        })
        quiz_data = gen.json()
        quiz_id = quiz_data["quiz_id"]

        # Mock questions always have correct_answer "B"; submit B for all
        answers = {q["id"]: "B" for q in quiz_data["questions"]}

        response = client.post(
            f"/api/quiz/{quiz_id}/submit",
            headers=auth_headers,
            json={"answers": answers}
        )
        assert response.status_code == 200
        result = response.json()
        assert result["score"] == result["total_questions"]
        assert result["percentage"] == 100.0
        assert "feedback" in result

    def test_submit_nonexistent_quiz(self, client: TestClient, auth_headers):
        response = client.post(
            "/api/quiz/99999/submit",
            headers=auth_headers,
            json={"answers": {}}
        )
        assert response.status_code == 404

    def test_submit_quiz_wrong_user(self, client: TestClient, auth_headers):
        client.post("/api/auth/register", json={
            "username": "otheruser",
            "email": "other@example.com",
            "password": "testpass123"
        })
        login_resp = client.post("/api/auth/login", data={
            "username": "otheruser",
            "password": "testpass123"
        })
        other_token = login_resp.json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        gen = client.post("/api/quiz/generate", headers=auth_headers, json={
            "topic": "Physics",
            "num_questions": 3
        })
        quiz_id = gen.json()["quiz_id"]

        response = client.post(
            f"/api/quiz/{quiz_id}/submit",
            headers=other_headers,
            json={"answers": {}}
        )
        assert response.status_code == 404
