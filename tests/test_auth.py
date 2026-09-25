import jwt
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.auth import ALGORITHM, SECRET_KEY
from app.database import Base, get_db
from app.main import app
from app.models import User, UserRole


@pytest.fixture
def db_session():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)

    with session_factory() as session:
        yield session

    Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def signup(client: TestClient, email: str = "ada@example.com"):
    return client.post(
        "/auth/signup",
        json={
            "first_name": "Ada",
            "last_name": "Lovelace",
            "email": email,
            "password": "correct-horse-battery-staple",
        },
    )


def test_signup_creates_attorney_with_hashed_password(
    client: TestClient, db_session: Session
):
    response = signup(client, "ADA@example.com")

    assert response.status_code == 201
    assert response.json() == {
        "id": 1,
        "first_name": "Ada",
        "last_name": "Lovelace",
        "email": "ada@example.com",
        "role": UserRole.ATTORNEY.value,
    }

    user = db_session.scalar(select(User))
    assert user is not None
    assert user.password != "correct-horse-battery-staple"
    assert user.password.startswith("$argon2")


def test_signup_rejects_duplicate_email(client: TestClient):
    assert signup(client).status_code == 201

    response = signup(client, "ADA@example.com")

    assert response.status_code == 409


def test_login_returns_access_token(client: TestClient):
    assert signup(client).status_code == 201

    response = client.post(
        "/auth/login",
        json={"email": "ADA@example.com", "password": "correct-horse-battery-staple"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    payload = jwt.decode(response.json()["access_token"], SECRET_KEY, algorithms=[ALGORITHM])
    assert payload["sub"] == "1"


def test_login_rejects_invalid_credentials(client: TestClient):
    assert signup(client).status_code == 201

    response = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json() == {"detail": "Invalid email or password"}


def test_me_returns_authenticated_user(client: TestClient):
    assert signup(client).status_code == 201
    login_response = client.post(
        "/auth/login",
        json={"email": "ada@example.com", "password": "correct-horse-battery-staple"},
    )

    response = client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {login_response.json()['access_token']}"},
    )

    assert response.status_code == 200
    assert response.json()["first_name"] == "Ada"
    assert response.json()["last_name"] == "Lovelace"


def test_me_rejects_missing_token(client: TestClient):
    response = client.get("/auth/me")

    assert response.status_code == 401
