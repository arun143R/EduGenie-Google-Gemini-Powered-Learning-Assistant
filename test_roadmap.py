from fastapi.testclient import TestClient


class TestRoadmap:
    def test_generate_roadmap_success(self, client: TestClient, auth_headers):
        response = client.post("/api/roadmap/generate", headers=auth_headers, json={
            "topic": "Data Science"
        })
        assert response.status_code == 200
        data = response.json()
        assert "roadmap_id" in data
        assert data["topic"] == "Data Science"
        assert len(data["steps"]) > 0

    def test_generate_roadmap_valid_steps(self, client: TestClient, auth_headers):
        response = client.post("/api/roadmap/generate", headers=auth_headers, json={
            "topic": "Web Development"
        })
        data = response.json()
        for step in data["steps"]:
            assert "step_number" in step
            assert "title" in step
            assert "description" in step

    def test_list_roadmaps(self, client: TestClient, auth_headers):
        client.post("/api/roadmap/generate", headers=auth_headers, json={
            "topic": "Machine Learning"
        })
        client.post("/api/roadmap/generate", headers=auth_headers, json={
            "topic": "Cloud Computing"
        })
        response = client.get("/api/roadmap/list", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2
        topics = [r["topic"] for r in data]
        assert "Machine Learning" in topics
        assert "Cloud Computing" in topics
