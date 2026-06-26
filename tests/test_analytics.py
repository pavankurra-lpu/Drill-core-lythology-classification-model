"""
=============================================================================
Analytics Endpoint Tests
=============================================================================
Tests for overview stats, timeline, lithology distribution, and reporting.
=============================================================================
"""

import uuid
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

pytestmark = [pytest.mark.asyncio, pytest.mark.unit]

# ---------------------------------------------------------------------------
# Mock Analytics Data
# ---------------------------------------------------------------------------

MOCK_OVERVIEW = {
    "total_predictions": 1250,
    "predictions_today": 47,
    "predictions_this_week": 312,
    "predictions_this_month": 1089,
    "average_confidence": 0.9124,
    "most_common_lithology": "Sandstone",
    "most_common_lithology_count": 423,
    "total_users": 28,
    "active_users_today": 12,
    "average_processing_time_ms": 1156.7,
    "total_datasets": 15,
    "unique_formations": 34,
    "unique_drill_sites": 22,
}

MOCK_TIMELINE = {
    "period": "last_30_days",
    "data": [
        {
            "date": (datetime.now(timezone.utc) - timedelta(days=i)).strftime("%Y-%m-%d"),
            "count": max(0, 40 - i * 2 + (i % 3) * 5),
            "average_confidence": round(0.88 + (i % 5) * 0.02, 4),
        }
        for i in range(30)
    ],
    "total": 1089,
    "trend": "increasing",
    "trend_percentage": 12.3,
}

MOCK_LITHOLOGY_DISTRIBUTION = {
    "total": 1250,
    "distribution": [
        {"class": "Sandstone", "count": 423, "percentage": 33.84, "avg_confidence": 0.9341},
        {"class": "Shale", "count": 287, "percentage": 22.96, "avg_confidence": 0.9012},
        {"class": "Limestone", "count": 198, "percentage": 15.84, "avg_confidence": 0.9234},
        {"class": "Granite", "count": 112, "percentage": 8.96, "avg_confidence": 0.9567},
        {"class": "Basalt", "count": 89, "percentage": 7.12, "avg_confidence": 0.9087},
        {"class": "Quartzite", "count": 56, "percentage": 4.48, "avg_confidence": 0.9445},
        {"class": "Mudstone", "count": 43, "percentage": 3.44, "avg_confidence": 0.8812},
        {"class": "Dolomite", "count": 23, "percentage": 1.84, "avg_confidence": 0.9123},
        {"class": "Conglomerate", "count": 14, "percentage": 1.12, "avg_confidence": 0.8756},
        {"class": "Coal", "count": 5, "percentage": 0.40, "avg_confidence": 0.9678},
    ],
}

MOCK_CONFIDENCE_STATS = {
    "average": 0.9124,
    "median": 0.9234,
    "min": 0.6012,
    "max": 0.9987,
    "std_dev": 0.0687,
    "percentile_25": 0.8756,
    "percentile_75": 0.9567,
    "high_confidence_count": 987,  # >= 0.90
    "medium_confidence_count": 213,  # 0.75-0.90
    "low_confidence_count": 50,  # < 0.75
}

MOCK_SITE_STATS = {
    "total_sites": 22,
    "sites": [
        {
            "drill_site": "Site-Alpha-7",
            "prediction_count": 89,
            "most_common_lithology": "Sandstone",
            "avg_confidence": 0.9234,
            "depth_range": {"min": 50.0, "max": 800.0},
        },
        {
            "drill_site": "Site-Beta-12",
            "prediction_count": 67,
            "most_common_lithology": "Shale",
            "avg_confidence": 0.9087,
            "depth_range": {"min": 100.0, "max": 1200.0},
        },
    ],
}


# ---------------------------------------------------------------------------
# Overview Analytics Tests
# ---------------------------------------------------------------------------

class TestGetOverview:
    """Tests for GET /api/v1/analytics/overview"""

    async def test_get_overview_success(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test retrieving system analytics overview."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_overview = AsyncMock(return_value=MOCK_OVERVIEW)

            response = await client.get(
                "/api/v1/analytics/overview",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "total_predictions" in data
        assert "predictions_today" in data
        assert "average_confidence" in data
        assert "most_common_lithology" in data
        assert data["total_predictions"] == 1250
        assert data["average_confidence"] == 0.9124

    async def test_get_overview_unauthenticated(self, client: AsyncClient):
        """Test that overview requires authentication."""
        response = await client.get("/api/v1/analytics/overview")
        assert response.status_code == 401

    async def test_get_overview_structure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that overview response has all required fields."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_overview = AsyncMock(return_value=MOCK_OVERVIEW)

            response = await client.get(
                "/api/v1/analytics/overview",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()

        required_fields = [
            "total_predictions",
            "predictions_today",
            "average_confidence",
            "most_common_lithology",
            "total_users",
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    async def test_get_overview_admin_sees_all_users(
        self, client: AsyncClient, admin_headers: dict
    ):
        """Test that admin overview includes all-user statistics."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_overview = AsyncMock(return_value=MOCK_OVERVIEW)

            response = await client.get(
                "/api/v1/analytics/overview",
                headers=admin_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data


# ---------------------------------------------------------------------------
# Timeline Analytics Tests
# ---------------------------------------------------------------------------

class TestGetPredictionTimeline:
    """Tests for GET /api/v1/analytics/timeline"""

    async def test_get_prediction_timeline_default(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting prediction timeline with default 30-day period."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_prediction_timeline = AsyncMock(return_value=MOCK_TIMELINE)

            response = await client.get(
                "/api/v1/analytics/timeline",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "period" in data
        assert "total" in data
        assert len(data["data"]) <= 30

    async def test_get_prediction_timeline_custom_period(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting timeline for a custom period."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_prediction_timeline = AsyncMock(
                return_value={
                    **MOCK_TIMELINE,
                    "period": "last_7_days",
                    "data": MOCK_TIMELINE["data"][:7],
                }
            )

            response = await client.get(
                "/api/v1/analytics/timeline",
                headers=auth_headers,
                params={"period": "7d"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) <= 7

    async def test_get_timeline_date_range_filter(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test filtering timeline by custom date range."""
        start_date = "2026-06-01"
        end_date = "2026-06-26"

        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_prediction_timeline = AsyncMock(return_value=MOCK_TIMELINE)

            response = await client.get(
                "/api/v1/analytics/timeline",
                headers=auth_headers,
                params={"start_date": start_date, "end_date": end_date},
            )

        assert response.status_code == 200

    async def test_get_timeline_each_point_has_required_fields(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that each timeline data point has required fields."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_prediction_timeline = AsyncMock(return_value=MOCK_TIMELINE)

            response = await client.get(
                "/api/v1/analytics/timeline",
                headers=auth_headers,
            )

        data = response.json()
        for point in data["data"]:
            assert "date" in point
            assert "count" in point

    async def test_get_timeline_invalid_period(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that invalid period parameter returns 422."""
        response = await client.get(
            "/api/v1/analytics/timeline",
            headers=auth_headers,
            params={"period": "invalid_period"},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# Lithology Distribution Tests
# ---------------------------------------------------------------------------

class TestGetLithologyDistribution:
    """Tests for GET /api/v1/analytics/distribution"""

    async def test_get_lithology_distribution(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting lithology class distribution."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_lithology_distribution = AsyncMock(
                return_value=MOCK_LITHOLOGY_DISTRIBUTION
            )

            response = await client.get(
                "/api/v1/analytics/distribution",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "distribution" in data
        assert "total" in data
        assert len(data["distribution"]) == 10
        assert data["total"] == 1250

    async def test_distribution_percentages_sum_to_100(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that distribution percentages approximately sum to 100."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_lithology_distribution = AsyncMock(
                return_value=MOCK_LITHOLOGY_DISTRIBUTION
            )

            response = await client.get(
                "/api/v1/analytics/distribution",
                headers=auth_headers,
            )

        data = response.json()
        total_percentage = sum(
            item["percentage"] for item in data["distribution"]
        )
        # Allow small floating point discrepancy
        assert abs(total_percentage - 100.0) < 0.1

    async def test_distribution_has_all_classes(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test that distribution includes all 10 lithology classes."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_lithology_distribution = AsyncMock(
                return_value=MOCK_LITHOLOGY_DISTRIBUTION
            )

            response = await client.get(
                "/api/v1/analytics/distribution",
                headers=auth_headers,
            )

        data = response.json()
        classes_in_response = {item["class"] for item in data["distribution"]}
        expected_classes = {
            "Sandstone", "Shale", "Limestone", "Granite", "Basalt",
            "Quartzite", "Mudstone", "Dolomite", "Conglomerate", "Coal",
        }
        assert classes_in_response == expected_classes

    async def test_distribution_sorted_by_count(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test distribution is sorted by count descending."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_lithology_distribution = AsyncMock(
                return_value=MOCK_LITHOLOGY_DISTRIBUTION
            )

            response = await client.get(
                "/api/v1/analytics/distribution",
                headers=auth_headers,
                params={"sort_by": "count"},
            )

        data = response.json()
        counts = [item["count"] for item in data["distribution"]]
        assert counts == sorted(counts, reverse=True)

    async def test_distribution_unauthenticated(self, client: AsyncClient):
        """Test distribution endpoint requires authentication."""
        response = await client.get("/api/v1/analytics/distribution")
        assert response.status_code == 401


# ---------------------------------------------------------------------------
# Confidence Statistics Tests
# ---------------------------------------------------------------------------

class TestConfidenceStatistics:
    """Tests for GET /api/v1/analytics/confidence"""

    async def test_get_confidence_statistics(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test retrieving confidence score statistics."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_confidence_statistics = AsyncMock(
                return_value=MOCK_CONFIDENCE_STATS
            )

            response = await client.get(
                "/api/v1/analytics/confidence",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "average" in data
        assert "median" in data
        assert "min" in data
        assert "max" in data
        assert 0 <= data["min"] <= data["average"] <= data["max"] <= 1.0


# ---------------------------------------------------------------------------
# Drill Site Analytics Tests
# ---------------------------------------------------------------------------

class TestSiteAnalytics:
    """Tests for GET /api/v1/analytics/sites"""

    async def test_get_site_analytics(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test getting per-drill-site analytics."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_site_statistics = AsyncMock(return_value=MOCK_SITE_STATS)

            response = await client.get(
                "/api/v1/analytics/sites",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "sites" in data
        assert "total_sites" in data
        assert data["total_sites"] > 0

    async def test_site_analytics_structure(
        self, client: AsyncClient, auth_headers: dict
    ):
        """Test each site record has required fields."""
        with patch("app.api.v1.endpoints.analytics.analytics_service") as mock_svc:
            mock_svc.get_site_statistics = AsyncMock(return_value=MOCK_SITE_STATS)

            response = await client.get(
                "/api/v1/analytics/sites",
                headers=auth_headers,
            )

        data = response.json()
        for site in data["sites"]:
            assert "drill_site" in site
            assert "prediction_count" in site
            assert "most_common_lithology" in site
