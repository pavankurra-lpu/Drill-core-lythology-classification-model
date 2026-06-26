"""
=============================================================================
Pytest Configuration & Fixtures
=============================================================================
Shared fixtures for the Lithology Classification System test suite.
Provides async test client, database setup/teardown, user fixtures, and more.
=============================================================================
"""

import asyncio
import io
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from PIL import Image
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

# ---------------------------------------------------------------------------
# Test database configuration
# ---------------------------------------------------------------------------
TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "sqlite+aiosqlite:///./test_lithology.db",
)

# ---------------------------------------------------------------------------
# Pytest configuration
# ---------------------------------------------------------------------------
pytest_plugins = ["pytest_asyncio"]


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "slow: Slow-running tests")
    config.addinivalue_line("markers", "ml: Machine learning tests")
    config.addinivalue_line("markers", "llm: LLM/RAG tests")


# ---------------------------------------------------------------------------
# Event loop fixture
# ---------------------------------------------------------------------------
@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Database fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture(scope="session")
async def test_engine():
    """Create async test database engine."""
    try:
        from app.core.database import Base

        engine = create_async_engine(
            TEST_DATABASE_URL,
            echo=False,
            future=True,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        yield engine

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)

        await engine.dispose()

    except ImportError:
        # App modules not available - use mock engine
        yield MagicMock()


@pytest_asyncio.fixture
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    """Create a test database session with transaction rollback."""
    try:
        from app.core.database import Base

        async_session = async_sessionmaker(
            test_engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

        async with async_session() as session:
            async with session.begin():
                yield session
                await session.rollback()
    except (ImportError, Exception):
        yield AsyncMock(spec=AsyncSession)


# ---------------------------------------------------------------------------
# Application fixtures
# ---------------------------------------------------------------------------
@pytest_asyncio.fixture
async def app():
    """Create FastAPI test application."""
    try:
        from app.main import app as fastapi_app
        from app.core.database import get_db

        async def override_get_db():
            yield AsyncMock(spec=AsyncSession)

        fastapi_app.dependency_overrides[get_db] = override_get_db
        yield fastapi_app
        fastapi_app.dependency_overrides.clear()

    except ImportError:
        from fastapi import FastAPI
        mock_app = FastAPI()
        yield mock_app


@pytest_asyncio.fixture
async def client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create async HTTP test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as ac:
        yield ac


# ---------------------------------------------------------------------------
# User fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def test_user_data() -> dict:
    """Regular test user data."""
    return {
        "email": "testuser@lithology.ai",
        "username": "testuser",
        "full_name": "Test User",
        "password": "TestPassword@123",
        "role": "user",
        "organization": "Test Organization",
    }


@pytest.fixture
def test_admin_data() -> dict:
    """Admin test user data."""
    return {
        "email": "admin.test@lithology.ai",
        "username": "testadmin",
        "full_name": "Test Administrator",
        "password": "AdminPassword@123",
        "role": "admin",
        "organization": "Lithology AI",
    }


@pytest_asyncio.fixture
async def test_user(db_session, test_user_data) -> dict:
    """Create and return a test user."""
    try:
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email=test_user_data["email"],
            username=test_user_data["username"],
            full_name=test_user_data["full_name"],
            hashed_password=get_password_hash(test_user_data["password"]),
            role=UserRole.USER,
            is_active=True,
            is_verified=True,
            organization=test_user_data["organization"],
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.flush()

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": "user",
            "password": test_user_data["password"],
        }
    except (ImportError, Exception):
        return {
            "id": str(uuid.uuid4()),
            "email": test_user_data["email"],
            "username": test_user_data["username"],
            "full_name": test_user_data["full_name"],
            "role": "user",
            "password": test_user_data["password"],
        }


@pytest_asyncio.fixture
async def test_admin(db_session, test_admin_data) -> dict:
    """Create and return an admin test user."""
    try:
        from app.models.user import User, UserRole
        from app.core.security import get_password_hash

        user = User(
            id=uuid.uuid4(),
            email=test_admin_data["email"],
            username=test_admin_data["username"],
            full_name=test_admin_data["full_name"],
            hashed_password=get_password_hash(test_admin_data["password"]),
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(user)
        await db_session.flush()

        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "full_name": user.full_name,
            "role": "admin",
            "password": test_admin_data["password"],
        }
    except (ImportError, Exception):
        return {
            "id": str(uuid.uuid4()),
            "email": test_admin_data["email"],
            "username": test_admin_data["username"],
            "full_name": test_admin_data["full_name"],
            "role": "admin",
            "password": test_admin_data["password"],
        }


# ---------------------------------------------------------------------------
# Auth token fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_token(test_user) -> str:
    """Generate JWT access token for test user."""
    try:
        from app.core.security import create_access_token

        return create_access_token(
            data={"sub": test_user["email"], "user_id": test_user["id"]}
        )
    except ImportError:
        return "mock_access_token_for_testing"


@pytest.fixture
def admin_token(test_admin) -> str:
    """Generate JWT access token for admin user."""
    try:
        from app.core.security import create_access_token

        return create_access_token(
            data={"sub": test_admin["email"], "user_id": test_admin["id"], "role": "admin"}
        )
    except ImportError:
        return "mock_admin_token_for_testing"


@pytest.fixture
def auth_headers(auth_token) -> dict:
    """Return authorization headers for regular user."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture
def admin_headers(admin_token) -> dict:
    """Return authorization headers for admin user."""
    return {"Authorization": f"Bearer {admin_token}"}


# ---------------------------------------------------------------------------
# Sample image fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_image_bytes() -> bytes:
    """Create a valid sample drill core image as bytes."""
    # Create a realistic-looking grayscale image
    img = Image.new("RGB", (300, 300), color=(180, 150, 120))

    # Add some texture to make it look like a core sample
    from PIL import ImageDraw, ImageFilter
    draw = ImageDraw.Draw(img)

    # Draw horizontal bands (simulating core layering)
    colors = [
        (160, 130, 100),
        (200, 180, 160),
        (140, 120, 90),
        (190, 170, 150),
        (170, 145, 110),
    ]
    band_height = 60
    for i, color in enumerate(colors):
        y0 = i * band_height
        y1 = y0 + band_height
        draw.rectangle([0, y0, 300, y1], fill=color)

    # Apply slight blur to look more natural
    img = img.filter(ImageFilter.GaussianBlur(radius=1))

    # Convert to bytes
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=90)
    buffer.seek(0)
    return buffer.getvalue()


@pytest.fixture
def sample_image_file(sample_image_bytes) -> io.BytesIO:
    """Return sample image as BytesIO file object."""
    return io.BytesIO(sample_image_bytes)


@pytest.fixture
def sample_png_bytes() -> bytes:
    """Create a sample PNG image."""
    img = Image.new("RGB", (224, 224), color=(100, 100, 100))
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# Sample prediction fixture
# ---------------------------------------------------------------------------
@pytest.fixture
def sample_prediction_data() -> dict:
    """Return sample prediction result data."""
    return {
        "id": str(uuid.uuid4()),
        "filename": "core_sample_test.jpg",
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
        "drill_site": "Site-Test-1",
        "processing_time_ms": 1234,
        "model_version": "efficientnet_b3_v1.0",
        "status": "completed",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


@pytest_asyncio.fixture
async def created_prediction(db_session, test_user, sample_prediction_data) -> dict:
    """Create a prediction record in the test database."""
    try:
        from app.models.prediction import Prediction, PredictionStatus

        prediction = Prediction(
            id=uuid.UUID(sample_prediction_data["id"]),
            user_id=uuid.UUID(test_user["id"]),
            filename=sample_prediction_data["filename"],
            original_filename=sample_prediction_data["filename"],
            file_path=f"uploads/images/{sample_prediction_data['filename']}",
            file_size=1024 * 1024,
            predicted_class=sample_prediction_data["predicted_class"],
            confidence=sample_prediction_data["confidence"],
            class_probabilities=sample_prediction_data["class_probabilities"],
            depth_m=sample_prediction_data["depth_m"],
            formation=sample_prediction_data["formation"],
            drill_site=sample_prediction_data["drill_site"],
            processing_time_ms=sample_prediction_data["processing_time_ms"],
            model_version=sample_prediction_data["model_version"],
            status=PredictionStatus.COMPLETED,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db_session.add(prediction)
        await db_session.flush()
        return sample_prediction_data
    except (ImportError, Exception):
        return sample_prediction_data


# ---------------------------------------------------------------------------
# Mock ML service fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def mock_ml_service():
    """Mock ML service for unit tests."""
    with patch("app.services.ml_service.MLService") as mock:
        instance = mock.return_value
        instance.predict = AsyncMock(
            return_value={
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
                "processing_time_ms": 1234,
                "model_version": "efficientnet_b3_v1.0",
            }
        )
        instance.preprocess_image = MagicMock(
            return_value=MagicMock(shape=(1, 3, 300, 300))
        )
        yield instance


@pytest.fixture
def mock_llm_service():
    """Mock LLM service for unit tests."""
    with patch("app.services.llm_service.LLMService") as mock:
        instance = mock.return_value
        instance.explain_prediction = AsyncMock(
            return_value={
                "explanation": (
                    "The sample shows classic sandstone characteristics including "
                    "granular texture, quartz-dominated mineralogy, and visible "
                    "cross-bedding structures indicating fluvial deposition."
                ),
                "confidence": 0.9234,
                "sources": ["geology_textbook_v2.pdf", "sandstone_handbook.pdf"],
                "metadata": {"tokens_used": 256, "model": "mistral-7b"},
            }
        )
        instance.answer_question = AsyncMock(
            return_value={
                "answer": "Sandstone forms from the compaction and cementation of sand grains.",
                "sources": ["geology_textbook_v2.pdf"],
                "confidence": 0.87,
            }
        )
        yield instance


# ---------------------------------------------------------------------------
# Environment fixtures
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def set_test_env(monkeypatch):
    """Set test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DEBUG", "true")
    monkeypatch.setenv("SECRET_KEY", "test-secret-key-for-unit-tests-minimum-32-chars-long")
    monkeypatch.setenv("DATABASE_URL", TEST_DATABASE_URL)
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379/0")
    monkeypatch.setenv("UPLOAD_DIR", "/tmp/test_uploads")
    monkeypatch.setenv("MODEL_DIR", "/tmp/test_models")
    monkeypatch.setenv("USE_GPU", "false")
    monkeypatch.setenv("EMAILS_ENABLED", "false")
