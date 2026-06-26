"""
=============================================================================
User Management Endpoint Tests
=============================================================================
Tests for profile retrieval, updating, password change, and admin operations.
=============================================================================
"""

import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]

# ---------------------------------------------------------------------------
# Profile Tests
# ---------------------------------------------------------------------------

class TestGetProfile:
    """Tests for GET /api/v1/users/profile and GET /api/v1/users/{user_id}"""

    async def test_get_profile_success(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test retrieving the authenticated user's profile."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.get_user_profile = AsyncMock(
                return_value={
                    "id": test_user["id"],
                    "email": test_user["email"],
                    "username": test_user["username"],
                    "full_name": test_user["full_name"],
                    "role": test_user["role"],
                    "is_active": True,
                    "is_verified": True,
                    "organization": "Test Org",
                    "bio": "Test bio",
                    "prediction_count": 15,
                    "joined_at": "2026-01-01T00:00:00Z",
                    "last_active": "2026-06-26T09:00:00Z",
                }
            )

            response = await client.get(
                "/api/v1/users/profile",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == test_user["email"]
        assert data["username"] == test_user["username"]
        assert "hashed_password" not in data
        assert "prediction_count" in data

    async def test_get_profile_unauthenticated(self, client: AsyncClient):
        """Test profile access requires authentication."""
        response = await client.get("/api/v1/users/profile")
        assert response.status_code == 401

    async def test_get_user_by_id_admin(
        self, client: AsyncClient, admin_headers: dict, test_user: dict
    ):
        """Test admin can retrieve any user by ID."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.get_user_by_id = AsyncMock(
                return_value={
                    "id": test_user["id"],
                    "email": test_user["email"],
                    "username": test_user["username"],
                    "full_name": test_user["full_name"],
                    "role": "user",
                    "is_active": True,
                }
            )

            response = await client.get(
                f"/api/v1/users/{test_user['id']}",
                headers=admin_headers,
            )

        assert response.status_code == 200

    async def test_get_user_by_id_forbidden_for_regular_user(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test regular users cannot access other users' profiles by ID."""
        other_user_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.get_user_by_id = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Not authorized to access this user profile",
                )
            )

            response = await client.get(
                f"/api/v1/users/{other_user_id}",
                headers=auth_headers,
            )

        assert response.status_code == 403

    async def test_get_user_not_found(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test retrieving non-existent user returns 404."""
        fake_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.get_user_by_id = AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail="User not found",
                )
            )

            response = await client.get(
                f"/api/v1/users/{fake_id}",
                headers=admin_headers,
            )

        assert response.status_code == 404


# ---------------------------------------------------------------------------
# Profile Update Tests
# ---------------------------------------------------------------------------

class TestUpdateProfile:
    """Tests for PUT/PATCH /api/v1/users/profile"""

    async def test_update_profile_success(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test successfully updating user profile."""
        update_data = {
            "full_name": "Updated Test Name",
            "organization": "Updated Org Corp",
            "bio": "Updated bio for testing purposes.",
        }

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.update_user_profile = AsyncMock(
                return_value={
                    "id": test_user["id"],
                    "email": test_user["email"],
                    "username": test_user["username"],
                    **update_data,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
            )

            response = await client.patch(
                "/api/v1/users/profile",
                headers=auth_headers,
                json=update_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["full_name"] == update_data["full_name"]
        assert data["organization"] == update_data["organization"]
        assert data["bio"] == update_data["bio"]

    async def test_update_profile_partial(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test partial profile update (only some fields)."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.update_user_profile = AsyncMock(
                return_value={
                    "id": test_user["id"],
                    "email": test_user["email"],
                    "full_name": "Only Name Updated",
                    "organization": "Test Organization",
                }
            )

            response = await client.patch(
                "/api/v1/users/profile",
                headers=auth_headers,
                json={"full_name": "Only Name Updated"},
            )

        assert response.status_code == 200

    async def test_update_profile_email_not_allowed(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that email cannot be changed through profile update."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.update_user_profile = AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail="Email cannot be changed through this endpoint",
                )
            )

            response = await client.patch(
                "/api/v1/users/profile",
                headers=auth_headers,
                json={"email": "new.email@example.com"},
            )

        assert response.status_code in [400, 422]

    async def test_update_profile_unauthenticated(self, client: AsyncClient):
        """Test profile update requires authentication."""
        response = await client.patch(
            "/api/v1/users/profile",
            json={"full_name": "New Name"},
        )
        assert response.status_code == 401

    async def test_update_profile_invalid_bio_length(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that excessively long bio is rejected."""
        response = await client.patch(
            "/api/v1/users/profile",
            headers=auth_headers,
            json={"bio": "x" * 2001},  # Exceeds max length
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Password Change Tests
# ---------------------------------------------------------------------------

class TestChangePassword:
    """Tests for POST /api/v1/users/change-password"""

    async def test_change_password_success(
        self, client: AsyncClient, auth_headers: dict, test_user: dict
    ):
        """Test successfully changing user password."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.change_password = AsyncMock(
                return_value={"message": "Password changed successfully"}
            )

            response = await client.post(
                "/api/v1/users/change-password",
                headers=auth_headers,
                json={
                    "current_password": test_user["password"],
                    "new_password": "NewSecurePass@789",
                    "confirm_password": "NewSecurePass@789",
                },
            )

        assert response.status_code == 200
        assert "success" in response.json()["message"].lower()

    async def test_change_password_wrong_current(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test password change fails with incorrect current password."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.change_password = AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail="Current password is incorrect",
                )
            )

            response = await client.post(
                "/api/v1/users/change-password",
                headers=auth_headers,
                json={
                    "current_password": "WrongCurrentPass@123",
                    "new_password": "NewPass@123",
                    "confirm_password": "NewPass@123",
                },
            )

        assert response.status_code == 400
        assert "incorrect" in response.json()["detail"].lower()

    async def test_change_password_mismatch(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test password change fails when passwords don't match."""
        response = await client.post(
            "/api/v1/users/change-password",
            headers=auth_headers,
            json={
                "current_password": "CurrentPass@123",
                "new_password": "NewPass@123",
                "confirm_password": "DifferentPass@456",
            },
        )
        assert response.status_code == 422

    async def test_change_password_weak_new_password(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that weak new password is rejected."""
        response = await client.post(
            "/api/v1/users/change-password",
            headers=auth_headers,
            json={
                "current_password": "CurrentPass@123",
                "new_password": "weak",
                "confirm_password": "weak",
            },
        )
        assert response.status_code == 422

    async def test_change_password_same_as_current(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that new password cannot be same as current password."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.change_password = AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail="New password must be different from current password",
                )
            )

            response = await client.post(
                "/api/v1/users/change-password",
                headers=auth_headers,
                json={
                    "current_password": "SamePass@123",
                    "new_password": "SamePass@123",
                    "confirm_password": "SamePass@123",
                },
            )

        assert response.status_code == 400

    async def test_change_password_unauthenticated(self, client: AsyncClient):
        """Test password change requires authentication."""
        response = await client.post(
            "/api/v1/users/change-password",
            json={
                "current_password": "OldPass@123",
                "new_password": "NewPass@123",
                "confirm_password": "NewPass@123",
            },
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Admin User Management Tests
# ---------------------------------------------------------------------------

class TestAdminUserManagement:
    """Tests for admin-only user management endpoints."""

    async def test_list_all_users_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test admin can list all users."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.list_users = AsyncMock(
                return_value={
                    "items": [
                        {
                            "id": str(uuid.uuid4()),
                            "email": "user1@test.com",
                            "username": "user1",
                            "role": "user",
                            "is_active": True,
                            "prediction_count": 5,
                        }
                    ],
                    "total": 1,
                    "page": 1,
                    "page_size": 10,
                    "pages": 1,
                }
            )

            response = await client.get(
                "/api/v1/users/",
                headers=admin_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data

    async def test_list_all_users_forbidden_for_regular(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test regular users cannot list all users."""
        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.list_users = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Admin access required",
                )
            )

            response = await client.get(
                "/api/v1/users/",
                headers=auth_headers,
            )

        assert response.status_code == 403

    async def test_deactivate_user_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test admin can deactivate a user account."""
        user_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.deactivate_user = AsyncMock(
                return_value={"message": f"User {user_id} deactivated", "id": user_id}
            )

            response = await client.post(
                f"/api/v1/users/{user_id}/deactivate",
                headers=admin_headers,
            )

        assert response.status_code == 200

    async def test_activate_user_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test admin can reactivate a deactivated user account."""
        user_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.activate_user = AsyncMock(
                return_value={"message": f"User {user_id} activated", "id": user_id}
            )

            response = await client.post(
                f"/api/v1/users/{user_id}/activate",
                headers=admin_headers,
            )

        assert response.status_code == 200

    async def test_change_user_role_admin(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test admin can change a user's role."""
        user_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.users.user_service") as mock_svc:
            mock_svc.update_user_role = AsyncMock(
                return_value={
                    "id": user_id,
                    "role": "admin",
                    "message": "Role updated successfully",
                }
            )

            response = await client.patch(
                f"/api/v1/users/{user_id}/role",
                headers=admin_headers,
                json={"role": "admin"},
            )

        assert response.status_code == 200
