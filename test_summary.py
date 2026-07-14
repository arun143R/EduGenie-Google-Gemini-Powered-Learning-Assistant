from fastapi.testclient import TestClient


class TestSummary:
    def test_summarize_success(self, client: TestClient, auth_headers):
        response = client.post("/api/summary/summarize", headers=auth_headers, json={
            "text": "Machine learning is a subset of artificial intelligence that enables systems to learn and improve from experience without being explicitly programmed.",
            "length": "short"
        })
        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert "original_length" in data
        assert "summary_length" in data
        assert data["original_length"] > 0
        assert data["summary_length"] > 0
