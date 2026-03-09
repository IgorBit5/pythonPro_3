from sqlalchemy import create_engine, Column, Integer, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import redis
import json
import os


DATABASE_URL = os.getenv("DATABASE_URL","postgresql://user:pass@localhost:5432/urlshortener")
REDIS_URL = os.getenv("REDIS_URL","redis://localhost:6379/0")

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Redis
redis_client = redis.Redis.from_url(REDIS_URL, decode_responses=True)

class Link(Base):
    __tablename__ = "links"
    id = Column(Integer, primary_key=True)
    short_code = Column(String, unique=True, index=True)
    original_url = Column(String)
    created_at = Column(DateTime, default=datetime.now)
    expires_at = Column(DateTime, nullable=True)
    clicks = Column(Integer, default=0)
    last_used = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    project = Column(String, nullable=True)


Base.metadata.create_all(bind=engine)


def cache_set(key, value, expire=10080):
    redis_client.setex(key, expire, json.dumps(value))

def cache_get(key):
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_delete(key):
    redis_client.delete(key)
    
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()