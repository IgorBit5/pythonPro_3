import pytest
import sys
import os
import tempfile

os.environ["TESTING"] = "true"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

db_fd, db_path = tempfile.mkstemp()
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi.testclient import TestClient
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import src.database
src.database.DATABASE_URL = f"sqlite:///{db_path}"
src.database.engine = create_engine(
    f"sqlite:///{db_path}",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)
src.database.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=src.database.engine)

# Заглушка для Redis
class MockRedis:
    def __init__(self):
        self.storage = {}
    def setex(self, key, expire, value):
        self.storage[key] = value
    def get(self, key):
        return self.storage.get(key)
    def delete(self, key):
        if key in self.storage:
            del self.storage[key]
    def ping(self):
        return True

src.database.redis_client = MockRedis()

from src.main import app
from src.database import Base, get_db


Base.metadata.create_all(bind=src.database.engine)

def override_get_db():
    db = src.database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture
def client():
    """Тестовый клиент с чистой БД перед каждым тестом"""
    # Очищаем БД
    Base.metadata.drop_all(bind=src.database.engine)
    Base.metadata.create_all(bind=src.database.engine)
    
    # Очищаем Redis
    src.database.redis_client.storage.clear()
    
    with TestClient(app) as test_client:
        yield test_client

@pytest.fixture
def db_session():
    """Сессия БД для прямого доступа в тестах"""
    db = src.database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@pytest.fixture
def sample_link(client):
    """Создает тестовую ссылку и возвращает ее код"""
    response = client.post("/links/shorten", json={"original_url": "https://example.com"})
    return response.json()["short_code"]