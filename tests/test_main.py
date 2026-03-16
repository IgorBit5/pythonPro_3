def test_create_short_url(client):
    """Тест создания короткой ссылки"""
    response = client.post("/links/shorten", json={"original_url": "https://example.com"})
    assert response.status_code == 201
    data = response.json()
    assert "short_code" in data
    assert data["original_url"] == "https://example.com"

def test_redirect(client):
    """Тест получения ссылки"""
    create_resp = client.post("/links/shorten", json={"original_url": "https://target.com"})
    short_code = create_resp.json()["short_code"]
    
    response = client.get(f"/links/{short_code}")
    assert response.status_code == 200
    assert response.json()["url"] == "https://target.com"

def test_create_with_custom_code(client):
    """Тест кастомного кода"""
    response = client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "custom_url": "mycode"
    })
    assert response.status_code == 201
    assert response.json()["short_code"] == "mycode"

def test_create_with_project(client):
    """Тест создания с проектом"""
    response = client.post("/links/shorten", json={
        "original_url": "https://example.com",
        "project": "test-project"
    })
    assert response.status_code == 201
    assert response.json()["project"] == "test-project"

def test_create_duplicate_url(client):
    """Тест дубликата URL"""
    response1 = client.post("/links/shorten", json={"original_url": "https://duplicate.com"})
    assert response1.status_code == 201

    response2 = client.post("/links/shorten", json={"original_url": "https://duplicate.com"})
    assert response2.status_code == 400
    assert "уже существует" in response2.json()["detail"].lower()

def test_duplicate_custom_code(client):
    """Тест дубликата кастомного кода"""
    client.post("/links/shorten", json={
        "original_url": "https://example1.com",
        "custom_url": "dup"
    })
    
    response = client.post("/links/shorten", json={
        "original_url": "https://example2.com",
        "custom_url": "dup"
    })
    assert response.status_code == 400

def test_get_link_stats(client):
    """Тест статистики ссылки"""

    create_resp = client.post("/links/shorten", json={"original_url": "https://example.com"})
    short_code = create_resp.json()["short_code"]
    
    response = client.get(f"/links/{short_code}/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://example.com"
    assert data["clicks"] == 0
    assert "created_at" in data

def test_update_link(client):
    """Тест обновления ссылки"""

    create_resp = client.post("/links/shorten", json={"original_url": "https://example.com"})
    short_code = create_resp.json()["short_code"]
    
    response = client.put(f"/links/{short_code}", json={"original_url": "https://updated.com"})
    assert response.status_code == 200
    assert response.json()["new_url"] == "https://updated.com"
    
    stats = client.get(f"/links/{short_code}/stats").json()
    assert stats["original_url"] == "https://updated.com"

def test_delete_link(client):
    """Тест удаления"""
    create_resp = client.post("/links/shorten", json={"original_url": "https://example.com"})
    short_code = create_resp.json()["short_code"]
    
    response = client.delete(f"/links/{short_code}")
    assert response.status_code == 204
    
    get_response = client.get(f"/links/{short_code}")
    assert get_response.status_code == 404

def test_increment_clicks(client):
    """Тест увеличения счетчика"""
    create_resp = client.post("/links/shorten", json={"original_url": "https://example.com"})
    short_code = create_resp.json()["short_code"]
    
    for _ in range(3):
        client.get(f"/links/{short_code}")
    
    stats = client.get(f"/links/{short_code}/stats").json()
    assert stats["clicks"] == 3

def test_get_project_links(client):
    """Тест получения ссылок проекта"""
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

def test_search_force(client):
    """Тест поиска по URL"""

    client.post("/links/shorten", json={"original_url": "https://searchme.com"})
    
    response = client.get("/links/search/force", params={"original_url": "https://searchme.com"})
    assert response.status_code == 200
    data = response.json()
    assert data["original_url"] == "https://searchme.com"
    assert data["method"] == "python_loop"

def test_get_all_links_debug(client):
    """Тест отладочного эндпоинта"""

    client.post("/links/shorten", json={"original_url": "https://debug1.com"})
    client.post("/links/shorten", json={"original_url": "https://debug2.com"})
    
    response = client.get("/links/debug/all")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] >= 2
    assert len(data["links"]) >= 2

def test_get_nonexistent_link(client):
    """Тест несуществующей ссылки"""
    response = client.get("/links/nonexistent")
    assert response.status_code == 404
    
    response = client.get("/links/nonexistent/stats")
    assert response.status_code == 404

def test_update_nonexistent_link(client):
    """Тест обновления несуществующей ссылки"""
    response = client.put("/links/nonexistent", json={"original_url": "https://example.com"})
    assert response.status_code == 404

def test_delete_nonexistent_link(client):
    """Тест удаления несуществующей ссылки"""
    response = client.delete("/links/nonexistent")
    assert response.status_code == 404

def test_root_endpoint(client):
    """Тест корневого эндпоинта"""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()