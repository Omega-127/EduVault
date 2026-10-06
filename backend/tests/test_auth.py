import pytest
from httpx import AsyncClient

from app.db.models import User


@pytest.mark.asyncio
async def test_registration_success(client: AsyncClient):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "newstudent@univ.edu",
            "password": "securepassword123",
            "role": "student",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newstudent@univ.edu"
    assert data["role"] == "student"
    assert "id" in data
    assert "hashed_pw" not in data


@pytest.mark.asyncio
async def test_duplicate_registration(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/register",
        json={
            "email": student_user.email,
            "password": "anotherpassword",
            "role": "student",
        },
    )
    assert response.status_code == 409
    assert "already exists" in response.json()["detail"]


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@university.edu",
            "password": "studentpassword123",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "student@university.edu"
    assert "refresh_token" in response.cookies


@pytest.mark.asyncio
async def test_login_invalid_password(client: AsyncClient, student_user: User):
    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "student@university.edu",
            "password": "wrongpassword999",
        },
    )
    assert response.status_code == 401
    assert "Invalid email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_jwt_validation_missing_token(client: AsyncClient):
    response = await client.get("/api/v1/documents/")
    assert response.status_code == 401
    assert "Authorization header is missing" in response.json()["detail"]


@pytest.mark.asyncio
async def test_jwt_validation_invalid_token(client: AsyncClient):
    response = await client.get(
        "/api/v1/documents/",
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_admin_authorization_success(client: AsyncClient, admin_auth_headers: dict):
    response = await client.get("/api/v1/admin/stats", headers=admin_auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_users" in data


@pytest.mark.asyncio
async def test_admin_authorization_forbidden_for_student(
    client: AsyncClient, student_auth_headers: dict
):
    response = await client.get("/api/v1/admin/stats", headers=student_auth_headers)
    assert response.status_code == 403
    assert "Admin role required" in response.json()["detail"]
