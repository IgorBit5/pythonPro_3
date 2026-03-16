from fastapi import status
from datetime import datetime, timedelta
import time
import pytest

class TestCreateLinks:
    """Тесты создания ссылок"""
    
    def test_create_simple_link(self, client):
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com"
        })
        assert response.status_code == 201
        data = response.json()
        assert "short_code" in data
        assert len(data["short_code"]) == 6
        assert data["original_url"] == "https://example.com"
    
    def test_create_with_custom_code(self, client):
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "custom_url": "custom123"
        })
        assert response.status_code == 201
        assert response.json()["short_code"] == "custom123"
    
    def test_create_with_project(self, client):
        response = client.post("/links/shorten", json={
            "original_url": "https://example.com",
            "project": "test-project"
        })
        assert response.status_code == 201
        assert response.json()["project"] == "test-project"
    
    def test_create_invalid_url(self, client):
        response = client.post("/links/shorten", json={
            "original_url": "not-a-url"
        })
        assert response.status_code == 201
        assert "short_code" in response.json()

class TestDuplicateLinks:
    """Тесты на дубликаты"""
    
    def test_duplicate_url(self, client):
        response1 = client.post("/links/shorten", json={
            "original_url": "https://duplicate.com"
        })
        assert response1.status_code == 201
        
        response2 = client.post("/links/shorten", json={
            "original_url": "https://duplicate.com"
        })
        assert response2.status_code == 400
        assert "уже существует" in response2.json()["detail"].lower()
    
    def test_duplicate_custom_code(self, client):
        client.post("/links/shorten", json={
            "original_url": "https://example1.com",
            "custom_url": "dup"
        })
        
        response = client.post("/links/shorten", json={
            "original_url": "https://example2.com",
            "custom_url": "dup"
        })
        assert response.status_code == 400
    
    def test_different_urls_same_project(self, client):
        project = "same-project"
        
        resp1 = client.post("/links/shorten", json={
            "original_url": "https://example1.com",
            "project": project
        })
        resp2 = client.post("/links/shorten", json={
            "original_url": "https://example2.com",
            "project": project
        })
        
        assert resp1.status_code == 201
        assert resp2.status_code == 201
        assert resp1.json()["project"] == project
        assert resp2.json()["project"] == project

class TestRedirect:
    """Тесты редиректа"""
    
    @pytest.fixture
    def sample_link(self, client):
        response = client.post("/links/shorten", json={"original_url": "https://example.com"})
        return response.json()["short_code"]
    
    def test_get_link(self, client, sample_link):
        response = client.get(f"/links/{sample_link}")
        assert response.status_code == 200
        assert "url" in response.json()
    
    def test_get_nonexistent_link(self, client):
        response = client.get("/links/nonexistent")
        assert response.status_code == 404
    
    def test_get_deleted_link(self, client, sample_link):
        client.delete(f"/links/{sample_link}")
        response = client.get(f"/links/{sample_link}")
        assert response.status_code == 404

class TestStats:
    """Тесты статистики"""
    
    @pytest.fixture
    def sample_link(self, client):
        response = client.post("/links/shorten", json={"original_url": "https://example.com"})
        return response.json()["short_code"]
    
    def test_get_stats(self, client, sample_link):
        response = client.get(f"/links/{sample_link}/stats")
        assert response.status_code == 200
        data = response.json()
        assert "original_url" in data
        assert "clicks" in data
        assert "created_at" in data
        assert data["clicks"] == 0
    
    def test_stats_after_clicks(self, client, sample_link):
        for _ in range(5):
            client.get(f"/links/{sample_link}")
        
        response = client.get(f"/links/{sample_link}/stats")
        assert response.json()["clicks"] == 5
    
    def test_stats_nonexistent(self, client):
        response = client.get("/links/nonexistent/stats")
        assert response.status_code == 404

class TestUpdate:
    """Тесты обновления"""
    
    @pytest.fixture
    def sample_link(self, client):
        response = client.post("/links/shorten", json={"original_url": "https://example.com"})
        return response.json()["short_code"]
    
    def test_update_link(self, client, sample_link):
        response = client.put(f"/links/{sample_link}", json={
            "original_url": "https://updated.com"
        })
        assert response.status_code == 200
        assert response.json()["new_url"] == "https://updated.com"
        
        stats = client.get(f"/links/{sample_link}/stats").json()
        assert stats["original_url"] == "https://updated.com"
    
    def test_update_nonexistent(self, client):
        response = client.put("/links/nonexistent", json={
            "original_url": "https://example.com"
        })
        assert response.status_code == 404
    
    def test_update_reset_clicks(self, client, sample_link):
        for _ in range(3):
            client.get(f"/links/{sample_link}")
        
        client.put(f"/links/{sample_link}", json={
            "original_url": "https://updated.com"
        })
        
        stats = client.get(f"/links/{sample_link}/stats").json()
        assert stats["clicks"] == 0

class TestDelete:
    """Тесты удаления"""
    
    @pytest.fixture
    def sample_link(self, client):
        response = client.post("/links/shorten", json={"original_url": "https://example.com"})
        return response.json()["short_code"]
    
    def test_delete_link(self, client, sample_link):
        response = client.delete(f"/links/{sample_link}")
        assert response.status_code == 204
        
        get_response = client.get(f"/links/{sample_link}")
        assert get_response.status_code == 404
    
    def test_delete_nonexistent(self, client):
        response = client.delete("/links/nonexistent")
        assert response.status_code == 404
    
    def test_delete_twice(self, client, sample_link):
        client.delete(f"/links/{sample_link}")
        response = client.delete(f"/links/{sample_link}")
        assert response.status_code == 404

class TestProjects:
    """Тесты проектов"""
    
    def test_get_project_links(self, client):
        project = "test-project"
        
        for i in range(3):
            client.post("/links/shorten", json={
                "original_url": f"https://example{i}.com",
                "project": project
            })
        
        response = client.get(f"/links/projects/{project}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for link in data:
            assert "short_code" in link
            assert "original_url" in link
    
    def test_get_empty_project(self, client):
        response = client.get("/links/projects/empty")
        assert response.status_code == 200
        assert response.json() == []

class TestSearch:
    """Тесты поиска"""
    
    def test_search_force(self, client):
        url = "https://searchme.com"
        client.post("/links/shorten", json={"original_url": url})
        
        response = client.get("/links/search/force", params={"original_url": url})
        assert response.status_code == 200
        data = response.json()
        assert data["original_url"] == url
        assert data["method"] == "python_loop"
    
    def test_search_not_found(self, client):
        response = client.get("/links/search/force", params={"original_url": "https://notfound.com"})
        assert response.status_code == 404

class TestDebug:
    """Отладочные эндпоинты"""
    
    def test_debug_all_links(self, client):
        for i in range(2):
            client.post("/links/shorten", json={
                "original_url": f"https://debug{i}.com"
            })
        
        response = client.get("/links/debug/all")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] >= 2
        assert len(data["links"]) >= 2

class TestRoot:
    """Корневой эндпоинт"""
    
    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "docs" in data

class TestConcurrency:
    """Тесты конкурентности"""
    
    def test_many_creations(self, client):
        codes = set()
        for i in range(10):
            response = client.post("/links/shorten", json={
                "original_url": f"https://example{i}.com"
            })
            assert response.status_code == 201
            codes.add(response.json()["short_code"])
        
        assert len(codes) == 10