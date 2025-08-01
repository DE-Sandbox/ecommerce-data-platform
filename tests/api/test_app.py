"""Tests for FastAPI application setup and structure."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class TestFastAPIApp:
    """Test FastAPI application setup."""

    def test_app_instance_creation(self) -> None:
        """Test that FastAPI app can be created."""
        from src.api.main import create_app

        app = create_app()
        assert isinstance(app, FastAPI)
        assert app.title == "E-commerce Data Platform API"
        assert app.version == "1.0.0"

    def test_app_has_cors_middleware(self) -> None:
        """Test that CORS middleware is configured."""
        from src.api.main import create_app

        app = create_app()
        middlewares = [str(m) for m in app.user_middleware]
        assert any("CORSMiddleware" in m for m in middlewares)

    def test_app_has_request_id_middleware(self) -> None:
        """Test that request ID middleware is configured."""
        from src.api.main import create_app

        app = create_app()
        middlewares = [str(m) for m in app.user_middleware]
        assert any("RequestIDMiddleware" in m for m in middlewares)

    def test_health_endpoint(self) -> None:
        """Test health check endpoint."""
        from src.api.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy"}

    def test_readiness_endpoint(self) -> None:
        """Test readiness check endpoint."""
        from src.api.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/ready")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "ready"
        assert "database" in data["checks"]
        assert "timestamp" in data

    def test_api_versioning_header(self) -> None:
        """Test API versioning via headers."""
        from src.api.main import create_app

        app = create_app()
        client = TestClient(app)

        # Test with version header
        response = client.get("/health", headers={"X-API-Version": "1.0"})
        assert response.status_code == 200

        # Test with unsupported version
        response = client.get("/health", headers={"X-API-Version": "99.0"})
        assert response.status_code == 400
        assert "version" in response.json()["detail"].lower()

    def test_openapi_docs_available(self) -> None:
        """Test that OpenAPI documentation is available."""
        from src.api.main import create_app

        app = create_app()
        client = TestClient(app)

        # Test OpenAPI JSON endpoint
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["openapi"].startswith("3.")

        # Test Swagger UI
        response = client.get("/docs")
        assert response.status_code == 200

        # Test ReDoc
        response = client.get("/redoc")
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_startup_event_registers_schemas(self) -> None:
        """Test that event schemas are registered on startup."""
        from src.api.main import create_app
        from src.events import get_registry

        app = create_app()

        # Simulate startup
        async with app.router.lifespan_context(app):
            registry = get_registry()
            event_types = registry.list_event_types()
            assert len(event_types) > 0
            assert "order.created" in event_types

    def test_correlation_id_in_response(self) -> None:
        """Test that correlation ID is included in responses."""
        from src.api.main import create_app

        app = create_app()
        client = TestClient(app)

        response = client.get("/health")
        assert "X-Correlation-ID" in response.headers
        assert len(response.headers["X-Correlation-ID"]) == 36  # UUID length
