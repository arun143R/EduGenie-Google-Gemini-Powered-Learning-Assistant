import pytest
import os
from typing import AsyncGenerator, Generator
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

os.environ["RUN_HF_MOCK"] = "True"
os.environ["GEMINI_API_KEY"] = ""
os.environ["SECRET_KEY"] = "test-secret-key-for-testing-only"
os.environ["DEBUG"] = "False"

from app.database import Base, get_db
from app.main import app
from app import models

TEST_DATABASE_URL = "sqlite:///./test_edugenie.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    with TestClient(app) as c:
        yield c


@pytest.fixture
def db() -> Generator[Session, None, None]:
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    response = client.post("/api/auth/login", data={
        "username": "testuser",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_cookies(client: TestClient) -> dict:
    client.post("/api/auth/register", json={
        "username": "cookietest",
        "email": "cookie@example.com",
        "password": "testpass123"
    })
    response = client.post("/api/auth/login", data={
        "username": "cookietest",
        "password": "testpass123"
    })
    cookies = response.cookies
    return {"access_token": cookies.get("access_token")}


@pytest.fixture
def registered_user(client: TestClient) -> dict:
    client.post("/api/auth/register", json={
        "username": "existinguser",
        "email": "existing@example.com",
        "password": "testpass123"
    })
    return {"username": "existinguser", "email": "existing@example.com"}
