from locust import HttpUser, task, between, tag
import random
import time

class CacheHitUser(HttpUser):
    """
    Тестирование кэша - многократные запросы одних и тех же ссылок
    """
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.hot_links = []
    
    def on_start(self):
        for i in range(5):
            response = self.client.post(
                "/links/shorten",
                json={"original_url": f"https://hotlink{i}.com"}
            )
            if response.status_code == 201:
                self.hot_links.append(response.json()["short_code"])
    
    @task
    def hit_cache(self):
        """Многократные запросы к одним и тем же ссылкам"""
        if not self.hot_links:
            return
        
        code = random.choice(self.hot_links)
        start_time = time.time()
        
        with self.client.get(
            f"/links/{code}",
            catch_response=True,
            name="GET [cached]"
        ) as response:
            if response.status_code == 200:
                response_time = (time.time() - start_time) * 1000
                if response_time < 10:  # Меньше 10мс - вероятно из кэша
                    response.success()
                else:
                    response.success()
            else:
                response.failure(f"Failed: {response.status_code}")

class CacheMissUser(HttpUser):
    """
    Тестирование без кэша - всегда новые ссылки
    """
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"
    
    @task
    def miss_cache(self):
        code = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz', k=6))
        start_time = time.time()
        
        with self.client.get(
            f"/links/{code}",
            catch_response=True,
            name="GET [uncached]"
        ) as response:
            if response.status_code == 404:
                # Ожидаемо для несуществующих
                response_time = (time.time() - start_time) * 1000
                response.success()
            else:
                response.failure(f"Unexpected: {response.status_code}")