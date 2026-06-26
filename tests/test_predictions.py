"""
=============================================================================
Prediction Endpoint Tests
=============================================================================
Tests for image upload, classification, retrieval, and deletion endpoints.
=============================================================================
"""

import io
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from PIL import Image

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_test_image(
    width: int = 300,
    height: int = 300,
    format: str = "JPEG",
    color: tuple = (180, 150, 120),
) -> bytes:
    """Generate an in-memory test image."""
    img = Image.new("RGB", (width, height), color=color)
    buffer = io.BytesIO()
    img.save(buffer, format=format)
    buffer.seek(0)
    return buffer.read()


MOCK_PREDICTION_RESPONSE = {
    "id": str(uuid.uuid4()),
    "filename": "core_sample_001.jpg",
    "predicted_class": "Sandstone",
    "confidence": 0.9234,
    "class_probabilities": {
        "Sandstone": 0.9234,
        "Shale": 0.0312,
        "Limestone": 0.0198,
        "Granite": 0.0089,
        "Basalt": 0.0067,
        "Quartzite": 0.0045,
        "Mudstone": 0.0023,
        "Dolomite": 0.0018,
        "Conglomerate": 0.0009,
        "Coal": 0.0005,
    },
    "depth_m": 125.5,
    "formation": "Morrison Formation",
    "drill_site": "Site-Alpha-7",
    "processing_time_ms": 1234,
    "model_version": "efficientnet_b3_v1.0",
    "status": "completed",
    "created_at": "2026-06-26T00:00:00Z",
    "updated_at": "2026-06-26T00:00:00Z",
}


# ---------------------------------------------------------------------------
# Image Upload & Classification Tests
# ---------------------------------------------------------------------------

class TestImageUpload:
    """Tests for POST /api/v1/predictions/upload"""

    async def test_upload_image_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        mock_ml_service,
    ):
        """Test successful image upload and classification."""
        image_bytes = create_test_image()

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.create_prediction = AsyncMock(
                return_value=MOCK_PREDICTION_RESPONSE
            )

            response = await client.post(
                "/api/v1/predictions/upload",
                headers=auth_headers,
                files={"file": ("core_sample.jpg", image_bytes, "image/jpeg")},
                data={
                    "depth_m": "125.5",
                    "formation": "Morrison Formation",
                    "drill_site": "Site-Alpha-7",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["predicted_class"] == "Sandstone"
        assert 0 <= data["confidence"] <= 1.0
        assert "class_probabilities" in data
        assert len(data["class_probabilities"]) == 10
        assert data["status"] == "completed"
        assert "id" in data

    async def test_upload_image_unauthenticated(self, client: AsyncClient):
        """Test that upload requires authentication."""
        image_bytes = create_test_image()

        response = await client.post(
            "/api/v1/predictions/upload",
            files={"file": ("core_sample.jpg", image_bytes, "image/jpeg")},
        )

        assert response.status_code == 401

    async def test_upload_invalid_file_type(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that non-image files are rejected."""
        fake_pdf = b"%PDF-1.4 malicious content here"

        response = await client.post(
            "/api/v1/predictions/upload",
            headers=auth_headers,
            files={"file": ("report.pdf", fake_pdf, "application/pdf")},
        )

        assert response.status_code == 422
        assert "invalid" in response.json()["detail"].lower() or \
               "unsupported" in response.json()["detail"].lower()

    async def test_upload_text_file_rejected(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that plain text files are rejected."""
        text_data = b"This is definitely not an image file"

        response = await client.post(
            "/api/v1/predictions/upload",
            headers=auth_headers,
            files={"file": ("data.txt", text_data, "text/plain")},
        )

        assert response.status_code == 422

    async def test_upload_file_too_large(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that files exceeding size limit are rejected."""
        # Create a large file (simulate > 50MB)
        large_data = b"x" * (51 * 1024 * 1024)  # 51MB

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.create_prediction = AsyncMock(
                side_effect=HTTPException(
                    status_code=413,
                    detail="File size exceeds maximum limit of 50MB",
                )
            )

            response = await client.post(
                "/api/v1/predictions/upload",
                headers=auth_headers,
                files={"file": ("huge.jpg", large_data, "image/jpeg")},
            )

        assert response.status_code == 413

    async def test_upload_png_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that PNG files are accepted."""
        png_bytes = create_test_image(format="PNG")

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.create_prediction = AsyncMock(
                return_value={**MOCK_PREDICTION_RESPONSE, "filename": "core.png"}
            )

            response = await client.post(
                "/api/v1/predictions/upload",
                headers=auth_headers,
                files={"file": ("core.png", png_bytes, "image/png")},
            )

        assert response.status_code == 201

    async def test_upload_with_metadata(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test image upload with all optional metadata."""
        image_bytes = create_test_image()

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.create_prediction = AsyncMock(
                return_value={
                    **MOCK_PREDICTION_RESPONSE,
                    "depth_m": 500.0,
                    "formation": "Permian Basin",
                    "drill_site": "Site-X-99",
                    "notes": "High quality sample",
                }
            )

            response = await client.post(
                "/api/v1/predictions/upload",
                headers=auth_headers,
                files={"file": ("sample.jpg", image_bytes, "image/jpeg")},
                data={
                    "depth_m": "500.0",
                    "formation": "Permian Basin",
                    "drill_site": "Site-X-99",
                    "notes": "High quality sample",
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["depth_m"] == 500.0

    async def test_upload_no_file(self, client: AsyncClient, auth_headers: dict):
        """Test that upload without a file is rejected."""
        response = await client.post(
            "/api/v1/predictions/upload",
            headers=auth_headers,
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Prediction Retrieval Tests
# ---------------------------------------------------------------------------

class TestGetPrediction:
    """Tests for GET /api/v1/predictions/{prediction_id}"""

    async def test_get_prediction_by_id(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_prediction: dict,
    ):
        """Test retrieving a specific prediction by ID."""
        prediction_id = created_prediction["id"]

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.get_prediction = AsyncMock(return_value=created_prediction)

            response = await client.get(
                f"/api/v1/predictions/{prediction_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == prediction_id
        assert data["predicted_class"] == "Sandstone"
        assert "class_probabilities" in data

    async def test_get_prediction_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test retrieving non-existent prediction returns 404."""
        fake_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.get_prediction = AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail="Prediction not found",
                )
            )

            response = await client.get(
                f"/api/v1/predictions/{fake_id}",
                headers=auth_headers,
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    async def test_get_prediction_unauthorized(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that users cannot access other users' predictions."""
        other_users_prediction_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.get_prediction = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Not authorized to access this prediction",
                )
            )

            response = await client.get(
                f"/api/v1/predictions/{other_users_prediction_id}",
                headers=auth_headers,
            )

        assert response.status_code == 403

    async def test_get_prediction_invalid_uuid(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that invalid UUID format returns 422."""
        response = await client.get(
            "/api/v1/predictions/not-a-valid-uuid",
            headers=auth_headers,
        )

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Prediction List Tests
# ---------------------------------------------------------------------------

class TestListPredictions:
    """Tests for GET /api/v1/predictions/"""

    async def test_list_predictions_paginated(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing predictions with pagination."""
        mock_predictions = [
            {**MOCK_PREDICTION_RESPONSE, "id": str(uuid.uuid4())}
            for _ in range(5)
        ]

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.list_predictions = AsyncMock(
                return_value={
                    "items": mock_predictions,
                    "total": 25,
                    "page": 1,
                    "page_size": 5,
                    "pages": 5,
                }
            )

            response = await client.get(
                "/api/v1/predictions/",
                headers=auth_headers,
                params={"page": 1, "page_size": 5},
            )

        assert response.status_code == 200
        data = response.json()
        assert "items" in data
        assert "total" in data
        assert len(data["items"]) == 5
        assert data["total"] == 25
        assert data["pages"] == 5

    async def test_list_predictions_default_pagination(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing predictions uses default pagination."""
        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.list_predictions = AsyncMock(
                return_value={
                    "items": [],
                    "total": 0,
                    "page": 1,
                    "page_size": 10,
                    "pages": 0,
                }
            )

            response = await client.get(
                "/api/v1/predictions/",
                headers=auth_headers,
            )

        assert response.status_code == 200

    async def test_list_predictions_filter_by_class(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test filtering predictions by lithology class."""
        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.list_predictions = AsyncMock(
                return_value={
                    "items": [MOCK_PREDICTION_RESPONSE],
                    "total": 1,
                    "page": 1,
                    "page_size": 10,
                    "pages": 1,
                }
            )

            response = await client.get(
                "/api/v1/predictions/",
                headers=auth_headers,
                params={"lithology_class": "Sandstone"},
            )

        assert response.status_code == 200
        data = response.json()
        for item in data["items"]:
            assert item["predicted_class"] == "Sandstone"

    async def test_list_predictions_unauthenticated(self, client: AsyncClient):
        """Test that listing predictions requires authentication."""
        response = await client.get("/api/v1/predictions/")
        assert response.status_code == 401

    async def test_list_predictions_sorted_by_date(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test listing predictions sorted by creation date."""
        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.list_predictions = AsyncMock(
                return_value={
                    "items": [MOCK_PREDICTION_RESPONSE],
                    "total": 1,
                    "page": 1,
                    "page_size": 10,
                    "pages": 1,
                }
            )

            response = await client.get(
                "/api/v1/predictions/",
                headers=auth_headers,
                params={"sort_by": "created_at", "sort_order": "desc"},
            )

        assert response.status_code == 200


# ---------------------------------------------------------------------------
# Prediction Deletion Tests
# ---------------------------------------------------------------------------

class TestDeletePrediction:
    """Tests for DELETE /api/v1/predictions/{prediction_id}"""

    async def test_delete_prediction_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_prediction: dict,
    ):
        """Test successful prediction deletion."""
        prediction_id = created_prediction["id"]

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.delete_prediction = AsyncMock(
                return_value={"message": "Prediction deleted successfully", "id": prediction_id}
            )

            response = await client.delete(
                f"/api/v1/predictions/{prediction_id}",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "deleted" in data["message"].lower()

    async def test_delete_prediction_not_found(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test deleting non-existent prediction returns 404."""
        fake_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.delete_prediction = AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail="Prediction not found",
                )
            )

            response = await client.delete(
                f"/api/v1/predictions/{fake_id}",
                headers=auth_headers,
            )

        assert response.status_code == 404

    async def test_delete_prediction_unauthorized(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test users cannot delete other users' predictions."""
        other_pred_id = str(uuid.uuid4())

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            from fastapi import HTTPException
            mock_svc.delete_prediction = AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail="Not authorized to delete this prediction",
                )
            )

            response = await client.delete(
                f"/api/v1/predictions/{other_pred_id}",
                headers=auth_headers,
            )

        assert response.status_code == 403

    async def test_delete_prediction_unauthenticated(self, client: AsyncClient):
        """Test deletion requires authentication."""
        response = await client.delete(
            f"/api/v1/predictions/{uuid.uuid4()}",
        )
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Prediction Update Tests
# ---------------------------------------------------------------------------

class TestUpdatePrediction:
    """Tests for PATCH /api/v1/predictions/{prediction_id}"""

    async def test_update_prediction_notes(
        self,
        client: AsyncClient,
        auth_headers: dict,
        created_prediction: dict,
    ):
        """Test updating prediction notes and metadata."""
        prediction_id = created_prediction["id"]
        update_data = {
            "notes": "Revised: High-quality sandstone with good porosity.",
            "depth_m": 130.0,
        }

        with patch("app.api.v1.endpoints.predictions.prediction_service") as mock_svc:
            mock_svc.update_prediction = AsyncMock(
                return_value={**MOCK_PREDICTION_RESPONSE, **update_data}
            )

            response = await client.patch(
                f"/api/v1/predictions/{prediction_id}",
                headers=auth_headers,
                json=update_data,
            )

        assert response.status_code == 200
        data = response.json()
        assert data["notes"] == update_data["notes"]
        assert data["depth_m"] == update_data["depth_m"]
