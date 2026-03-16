from locust import HttpUser, task, between, tag
import random
import string
import json
from datetime import datetime, timedelta

class ShortLinkUser(HttpUser):
    """
    Пользователь для нагрузочного тестирования сервиса коротких ссылок
    """
    wait_time = between(1, 3)  # Ждем 1-3 секунды между задачами
    host = "http://localhost:8000"  # Адрес тестируемого сервера
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_links = []  # Храним созданные ссылки
        self.test_data = self.generate_test_data()
    
    def generate_test_data(self):
        """Генерирует тестовые данные"""
        return {
            "urls": [
                f"https://example{i}.com/very/long/path/with/parameters?q={i}"
                for i in range(100)
            ],
            "projects": ["test", "prod", "dev", "marketing", "sales"],
            "custom_codes": [
                ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                for _ in range(50)
            ]
        }
    
    def on_start(self):
        """Выполняется при старте каждого пользователя"""
        # Создаем несколько ссылок для дальнейшего использования
        for _ in range(3):
            self.create_link()
    
    def generate_short_code(self):
        """Генерирует случайный код"""
        return ''.join(random.choices(string.ascii_letters + string.digits, k=6))
    
    @task(10)  # Высокий приоритет
    @tag("create", "high")
    def create_link(self):
        """Массовое создание ссылок"""
        url = random.choice(self.test_data["urls"])
        payload = {"original_url": url}
        
        # Иногда добавляем project
        if random.random() < 0.3:
            payload["project"] = random.choice(self.test_data["projects"])
        
        # Иногда добавляем expires_at
        if random.random() < 0.2:
            expires_at = (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
            payload["expires_at"] = expires_at
        
        # Иногда используем кастомный код
        if random.random() < 0.1:
            payload["custom_url"] = random.choice(self.test_data["custom_codes"])
        
        with self.client.post(
            "/links/shorten",
            json=payload,
            catch_response=True,
            name="POST /links/shorten [create]"
        ) as response:
            if response.status_code == 201:
                data = response.json()
                self.created_links.append(data["short_code"])
                response.success()
            elif response.status_code == 400:
                # Дубликат - тоже успех (бизнес-логика работает)
                response.success()
            else:
                response.failure(f"Unexpected status: {response.status_code}")
    
    @task(8)
    @tag("get", "medium")
    def get_link(self):
        """Получение ссылок (симуляция переходов)"""
        if not self.created_links:
            return
        
        code = random.choice(self.created_links)
        with self.client.get(
            f"/links/{code}",
            catch_response=True,
            name="GET /links/{code} [get]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get link: {response.status_code}")
    
    @task(3)
    @tag("stats", "low")
    def get_stats(self):
        """Получение статистики"""
        if not self.created_links:
            return
        
        code = random.choice(self.created_links)
        with self.client.get(
            f"/links/{code}/stats",
            catch_response=True,
            name="GET /links/{code}/stats [stats]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to get stats: {response.status_code}")
    
    @task(2)
    @tag("update", "low")
    def update_link(self):
        """Обновление ссылок"""
        if not self.created_links or len(self.created_links) < 2:
            return
        
        code = random.choice(self.created_links)
        new_url = f"https://updated-{random.randint(1, 1000)}.com"
        
        with self.client.put(
            f"/links/{code}",
            json={"original_url": new_url},
            catch_response=True,
            name="PUT /links/{code} [update]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to update: {response.status_code}")
    
    @task(1)
    @tag("delete", "low")
    def delete_link(self):
        """Удаление ссылок"""
        if not self.created_links or len(self.created_links) < 3:
            return
        
        code = self.created_links.pop(0)  # Удаляем самую старую
        with self.client.delete(
            f"/links/{code}",
            catch_response=True,
            name="DELETE /links/{code} [delete]"
        ) as response:
            if response.status_code == 204:
                response.success()
            else:
                response.failure(f"Failed to delete: {response.status_code}")
    
    @task(2)
    @tag("search", "medium")
    def search_links(self):
        """Поиск ссылок"""
        project = random.choice(self.test_data["projects"])
        with self.client.get(
            f"/links/projects/{project}",
            catch_response=True,
            name="GET /links/projects/{project} [search]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Failed to search: {response.status_code}")
    
    @task(1)
    @tag("debug", "low")
    def debug_all(self):
        """Отладочный эндпоинт"""
        with self.client.get(
            "/links/debug/all",
            catch_response=True,
            name="GET /links/debug/all [debug]"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Debug failed: {response.status_code}")


class ReadOnlyUser(HttpUser):
    """
    Пользователь только для чтения (симулирует просмотрщиков)
    """
    wait_time = between(0.5, 2)
    host = "http://localhost:8000"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_codes = []
    
    def on_start(self):
        # Получаем список существующих ссылок
        response = self.client.get("/links/debug/all")
        if response.status_code == 200:
            data = response.json()
            self.test_codes = [link["short_code"] for link in data["links"][:10]]
    
    @task(10)
    @tag("read", "get")
    def get_existing_link(self):
        """Получение существующих ссылок"""
        if not self.test_codes:
            return
        
        code = random.choice(self.test_codes)
        self.client.get(f"/links/{code}", name="GET /links/{code} [read]")
    
    @task(3)
    @tag("read", "stats")
    def get_existing_stats(self):
        """Статистика существующих ссылок"""
        if not self.test_codes:
            return
        
        code = random.choice(self.test_codes)
        self.client.get(f"/links/{code}/stats", name="GET /links/{code}/stats [read]")


class MixedWorkloadUser(HttpUser):
    """
    Смешанная нагрузка: чтение и запись
    """
    wait_time = between(0.1, 1)
    host = "http://localhost:8000"
    
    @task(70)
    def read(self):
        """70% - чтение"""
        code = ''.join(random.choices(string.ascii_letters + string.digits, k=6))
        self.client.get(f"/links/{code}", name="GET [read 70%]")
    
    @task(20)
    def write(self):
        """20% - запись"""
        url = f"https://example{random.randint(1, 10000)}.com"
        self.client.post("/links/shorten", json={"original_url": url}, name="POST [write 20%]")
    
    @task(10)
    def other(self):
        """10% - остальное"""
        endpoint = random.choice(["/", "/links/debug/all"])
        self.client.get(endpoint, name=f"GET {endpoint} [other 10%]")