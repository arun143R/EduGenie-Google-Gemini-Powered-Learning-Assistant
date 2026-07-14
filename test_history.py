from fastapi.testclient import TestClient


class TestHistory:
    def test_list_history_empty(self, client: TestClient, auth_headers):
        response = client.get("/api/history/list", headers=auth_headers)
        assert response.status_code == 200
        assert response.json() == []

    def test_list_history_after_activity(self, client: TestClient, auth_headers):
        client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is calculus?"
        })
        response = client.get("/api/history/list", headers=auth_headers)
        assert response.status_code == 200
        entries = response.json()
        assert len(entries) >= 1
        assert entries[0]["activity_type"] == "qna"

    def test_history_response_no_user_id(self, client: TestClient, auth_headers):
        client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is Python?"
        })
        response = client.get("/api/history/list", headers=auth_headers)
        entry = response.json()[0]
        assert "user_id" not in entry

    def test_delete_history_entry(self, client: TestClient, auth_headers):
        client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is chemistry?"
        })
        list_resp = client.get("/api/history/list", headers=auth_headers)
        entry_id = list_resp.json()[0]["id"]

        delete_resp = client.delete(f"/api/history/delete/{entry_id}", headers=auth_headers)
        assert delete_resp.status_code == 200
        assert "successfully deleted" in delete_resp.json()["message"].lower()

        list_resp2 = client.get("/api/history/list", headers=auth_headers)
        ids = [e["id"] for e in list_resp2.json()]
        assert entry_id not in ids

    def test_delete_nonexistent_history(self, client: TestClient, auth_headers):
        response = client.delete("/api/history/delete/99999", headers=auth_headers)
        assert response.status_code == 404

    def test_filter_history_by_type(self, client: TestClient, auth_headers):
        client.post("/api/qna/ask", headers=auth_headers, json={
            "question": "What is astronomy?"
        })
        response = client.get("/api/history/list?activity_type=qna", headers=auth_headers)
        for entry in response.json():
            assert entry["activity_type"] == "qna"

        response = client.get("/api/history/list?activity_type=explain", headers=auth_headers)
        for entry in response.json():
            assert entry["activity_type"] == "explain"
