"""
=============================================================================
Authentication Endpoint Tests
=============================================================================
Tests for user registration, login, token refresh, and profile endpoints.
=============================================================================
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]


# ---------------------------------------------------------------------------
# Registration Tests
# ---------------------------------------------------------------------------

class TestUserRegistration:
    """Tests for POST /api/v1/auth/register"""

    async def test_register_success(self, client: AsyncClient):
        """Test successful user registration with valid data."""
        payload = {
            "email": "newuser@lithology.ai",
            "username": "newuser",
            "full_name": "New User",
            "password": "SecurePass@123",
            "organization": "Mining Corp",
        }

        with patch("app.api.v1.endpoints.auth.user_service") as mock_svc:
            mock_svc.create_user = AsyncMock(
                return_value={
                    "id": str(uuid.uuid4()),
                    "email": payload["email"],
                    "username": payload["username"],
                    "full_name": payload["full_name"],
                    "role": "user",
                    "is_active": True,
                    "is_verified": False,
                    "created_at": "2026-06-26T00:00:00Z",
                }
            )

            response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["email"] == payload["email"]
        assert data["username"] == payload["username"]
        assert "password" not in data
        assert "hashed_password" not in data

    async def test_register_duplicate_email(self, client: AsyncClient):
        """Test registration fails when email already exists."""
        payload = {
            "email": "existing@lithology.ai",
            "username": "existinguser",
            "full_name": "Existing User",
            "password": "SecurePass@123",
        }

        with patch("app.api.v1.endpoints.auth.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.create_user = AsyncMock(
                side_effect=HTTPException(
                    status_code=409,
                    detail="User with this email already exists",
                )
            )

            response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    async def test_register_invalid_email(self, client: AsyncClient):
        """Test registration fails with invalid email format."""
        payload = {
            "email": "not-a-valid-email",
            "username": "testuser",
            "full_name": "Test User",
            "password": "SecurePass@123",
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_weak_password(self, client: AsyncClient):
        """Test registration fails with weak password."""
        payload = {
            "email": "valid@lithology.ai",
            "username": "validuser",
            "full_name": "Valid User",
            "password": "123",  # Too weak
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_missing_required_fields(self, client: AsyncClient):
        """Test registration fails when required fields are missing."""
        payload = {
            "email": "valid@lithology.ai",
            # Missing username, full_name, password
        }

        response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 422

    async def test_register_duplicate_username(self, client: AsyncClient):
        """Test registration fails when username already exists."""
        payload = {
            "email": "unique@lithology.ai",
            "username": "taken_username",
            "full_name": "Test User",
            "password": "SecurePass@123",
        }

        with patch("app.api.v1.endpoints.auth.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.create_user = AsyncMock(
                side_effect=HTTPException(
                    status_code=409,
                    detail="Username is already taken",
                )
            )

            response = await client.post("/api/v1/auth/register", json=payload)

        assert response.status_code == 409
        assert "taken" in response.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Login Tests
# ---------------------------------------------------------------------------

class TestUserLogin:
    """Tests for POST /api/v1/auth/login"""

    async def test_login_success(self, client: AsyncClient, test_user: dict):
        """Test successful login with correct credentials."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            mock_svc.authenticate_user = AsyncMock(
                return_value={
                    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.mock",
                    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.refresh_mock",
                    "token_type": "bearer",
                    "expires_in": 1800,
                    "user": {
                        "id": test_user["id"],
                        "email": test_user["email"],
                        "username": test_user["username"],
                        "role": test_user["role"],
                    },
                }
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user["email"],
                    "password": test_user["password"],
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    async def test_login_wrong_password(self, client: AsyncClient, test_user: dict):
        """Test login fails with incorrect password."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.authenticate_user = AsyncMock(
                side_effect=HTTPException(
                    status_code=401,
                    detail="Invalid email or password",
                )
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": test_user["email"],
                    "password": "WrongPassword@123",
                },
            )

        assert response.status_code == 401
        assert "invalid" in response.json()["detail"].lower()

    async def test_login_nonexistent_user(self, client: AsyncClient):
        """Test login fails for non-existent user."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.authenticate_user = AsyncMock(
                side_effect=HTTPException(
                    status_code=401,
                    detail="Invalid email or password",
                )
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "nobody@example.com",
                    "password": "AnyPassword@123",
                },
            )

        assert response.status_code == 401

    async def test_login_inactive_user(self, client: AsyncClient):
        """Test login fails for inactive/disabled account."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.authenticate_user = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Account is disabled. Please contact support.",
                )
            )

            response = await client.post(
                "/api/v1/auth/login",
                json={
                    "email": "inactive@lithology.ai",
                    "password": "Password@123",
                },
            )

        assert response.status_code == 403

    async def test_login_missing_email(self, client: AsyncClient):
        """Test login fails when email is missing."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"password": "Password@123"},
        )
        assert response.status_code == 422

    async def test_login_missing_password(self, client: AsyncClient):
        """Test login fails when password is missing."""
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": "user@lithology.ai"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Current User Tests
# ---------------------------------------------------------------------------

class TestGetCurrentUser:
    """Tests for GET /api/v1/auth/me"""

    async def test_get_me_authenticated(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test getting current user profile when authenticated."""
        with patch("app.api.v1.endpoints.auth.get_current_user") as mock_dep:
            mock_dep.return_value = {
                "id": test_user["id"],
                "email": test_user["email"],
                "username": test_user["username"],
                "full_name": test_user["full_name"],
                "role": test_user["role"],
                "is_active": True,
                "is_verified": True,
            }

            response = await client.get(
                "/api/v1/auth/me",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert "hashed_password" not in data

    async def test_get_me_unauthenticated(self, client: AsyncClient):
        """Test getting current user without authentication fails."""
        response = await client.get("/api/v1/auth/me")

        assert response.status_code == 401
        assert "not authenticated" in response.json()["detail"].lower() or \
               "authorization" in str(response.json()).lower()

    async def test_get_me_invalid_token(self, client: AsyncClient):
        """Test getting current user with invalid token fails."""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.jwt.token"},
        )

        assert response.status_code == 401

    async def test_get_me_expired_token(self, client: AsyncClient):
        """Test getting current user with expired token fails."""
        # Expired token (crafted for testing)
        expired_token = (
            "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
            "eyJzdWIiOiJ1c2VyQHRlc3QuY29tIiwiZXhwIjoxNjAwMDAwMDAwfQ."
            "invalid_signature"
        )

        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {expired_token}"},
        )

        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Token Refresh Tests
# ---------------------------------------------------------------------------

class TestTokenRefresh:
    """Tests for POST /api/v1/auth/refresh"""

    async def test_refresh_token_success(self, client: AsyncClient):
        """Test successful token refresh."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            mock_svc.refresh_access_token = AsyncMock(
                return_value={
                    "access_token": "new.access.token",
                    "token_type": "bearer",
                    "expires_in": 1800,
                }
            )

            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "valid.refresh.token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    async def test_refresh_token_invalid(self, client: AsyncClient):
        """Test token refresh fails with invalid refresh token."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.refresh_access_token = AsyncMock(
                side_effect=HTTPException(
                    status_code=401,
                    detail="Invalid or expired refresh token",
                )
            )

            response = await client.post(
                "/api/v1/auth/refresh",
                json={"refresh_token": "invalid.refresh.token"},
            )

        assert response.status_code == 401

    async def test_refresh_token_missing(self, client: AsyncClient):
        """Test token refresh fails when refresh token is missing."""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Logout Tests
# ---------------------------------------------------------------------------

class TestLogout:
    """Tests for POST /api/v1/auth/logout"""

    async def test_logout_success(self, client: AsyncClient, auth_headers: dict):
        """Test successful logout."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            mock_svc.logout = AsyncMock(return_value={"message": "Successfully logged out"})

            response = await client.post(
                "/api/v1/auth/logout",
                headers=auth_headers,
            )

        assert response.status_code == 200
        assert "logged out" in response.json()["message"].lower()

    async def test_logout_unauthenticated(self, client: AsyncClient):
        """Test logout without authentication fails."""
        response = await client.post("/api/v1/auth/logout")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Password Reset Tests
# ---------------------------------------------------------------------------

class TestPasswordReset:
    """Tests for password reset flow."""

    async def test_request_password_reset(self, client: AsyncClient):
        """Test requesting a password reset email."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            mock_svc.request_password_reset = AsyncMock(
                return_value={
                    "message": "Password reset email sent if account exists"
                }
            )

            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "user@lithology.ai"},
            )

        # Should always return 200 (security: don't reveal if email exists)
        assert response.status_code == 200

    async def test_reset_password_success(self, client: AsyncClient):
        """Test successful password reset with valid token."""
        with patch("app.api.v1.endpoints.auth.auth_service") as mock_svc:
            mock_svc.reset_password = AsyncMock(
                return_value={"message": "Password reset successfully"}
            )

            response = await client.post(
                "/api/v1/auth/reset-password",
                json={
                    "token": "valid_reset_token",
                    "new_password": "NewSecurePass@456",
                },
            )

        assert response.status_code == 200
