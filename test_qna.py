from fastapi.testclient import TestClient


class TestQnA:
    def test_ask_question_success(self, client: TestClient, auth_headers):
        response = client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is machine learning?"
        })
        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert "answer" in data
        assert data["question"] == "What is machine learning?"

    def test_ask_question_logs_history(self, client: TestClient, auth_headers):
        client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is deep learning?"
        })
        response = client.get("/api/history/list", headers=auth_headers)
        assert response.status_code == 200
        entries = response.json()
        types = [e["activity_type"] for e in entries]
        assert "qna" in types
