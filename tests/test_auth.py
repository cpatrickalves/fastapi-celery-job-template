"""
Tests for API Key Authentication Module.

This module tests the authentication functionality including:
- API key parsing from environment
- API key validation
- Error handling for missing/invalid keys
- Integration tests for protected endpoints
"""

import asyncio
from unittest.mock import patch, MagicMock

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from app.api.auth import get_api_keys, verify_api_key


class TestGetApiKeys:
    """Tests for the get_api_keys function."""

    def test_returns_empty_set_when_no_keys_configured(self):
        """Should return empty set when API_KEYS is not set."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = ""
            result = get_api_keys()
            assert result == set()

    def test_returns_single_key(self):
        """Should return set with single key."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "my-secret-key"
            result = get_api_keys()
            assert result == {"my-secret-key"}

    def test_returns_multiple_keys(self):
        """Should parse comma-separated keys into set."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "key1,key2,key3"
            result = get_api_keys()
            assert result == {"key1", "key2", "key3"}

    def test_strips_whitespace_from_keys(self):
        """Should strip whitespace from keys."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = " key1 , key2 , key3 "
            result = get_api_keys()
            assert result == {"key1", "key2", "key3"}

    def test_ignores_empty_keys(self):
        """Should ignore empty keys from parsing."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "key1,,key2,  ,key3"
            result = get_api_keys()
            assert result == {"key1", "key2", "key3"}


class TestVerifyApiKey:
    """Tests for the verify_api_key dependency."""

    def test_returns_key_when_valid(self):
        """Should return the API key when it's valid."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "valid-key"
            result = asyncio.run(verify_api_key("valid-key"))
            assert result == "valid-key"

    def test_raises_401_for_invalid_key(self):
        """Should raise 401 Unauthorized for invalid API key."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "valid-key"
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(verify_api_key("invalid-key"))
            assert exc_info.value.status_code == 401
            assert exc_info.value.detail == "Invalid API key"

    def test_raises_500_when_no_keys_configured(self):
        """Should raise 500 when no API keys are configured."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = ""
            with pytest.raises(HTTPException) as exc_info:
                asyncio.run(verify_api_key("any-key"))
            assert exc_info.value.status_code == 500
            assert exc_info.value.detail == "API key authentication not configured"

    def test_accepts_any_valid_key_from_multiple(self):
        """Should accept any key from the configured set."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "key1,key2,key3"
            assert asyncio.run(verify_api_key("key1")) == "key1"
            assert asyncio.run(verify_api_key("key2")) == "key2"
            assert asyncio.run(verify_api_key("key3")) == "key3"


class TestApiKeyEndpointIntegration:
    """Integration tests for API key authentication on endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client with mocked dependencies."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "test-api-key"
            # Import app after patching to ensure auth uses mocked settings
            from fastapi import FastAPI, Depends
            from app.api.auth import verify_api_key

            # Create a minimal test app
            test_app = FastAPI()

            @test_app.get("/protected")
            def protected_route(api_key: str = Depends(verify_api_key)):
                return {"message": "success", "api_key": api_key}

            @test_app.get("/public")
            def public_route():
                return {"message": "public"}

            yield TestClient(test_app)

    def test_protected_endpoint_returns_403_without_api_key(self, client):
        """Should return 403 when no API key is provided."""
        response = client.get("/protected")
        assert response.status_code == 403
        assert "Not authenticated" in response.json()["detail"]

    def test_protected_endpoint_returns_401_with_invalid_key(self, client):
        """Should return 401 when invalid API key is provided."""
        response = client.get("/protected", headers={"X-API-Key": "wrong-key"})
        assert response.status_code == 401
        assert response.json()["detail"] == "Invalid API key"

    def test_protected_endpoint_returns_200_with_valid_key(self, client):
        """Should return 200 when valid API key is provided."""
        response = client.get("/protected", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
        assert response.json()["message"] == "success"

    def test_public_endpoint_works_without_api_key(self, client):
        """Should allow access to public endpoints without API key."""
        response = client.get("/public")
        assert response.status_code == 200
        assert response.json()["message"] == "public"


class TestJobsEndpointAuthentication:
    """Integration tests for /jobs endpoint authentication with POST and GET."""

    @pytest.fixture
    def client(self):
        """Create test client simulating jobs endpoints."""
        with patch("app.api.auth.settings") as mock_settings:
            mock_settings.API_KEYS = "test-api-key"

            from fastapi import FastAPI, Depends
            from app.api.auth import verify_api_key

            app = FastAPI()

            @app.post("/jobs/example")
            def submit_job(api_key: str = Depends(verify_api_key)):
                return {"job_id": "123", "status": "pending"}

            @app.get("/jobs/{job_id}")
            def get_job(job_id: str, api_key: str = Depends(verify_api_key)):
                return {"job_id": job_id, "status": "completed"}

            yield TestClient(app)

    def test_post_job_requires_api_key(self, client):
        """POST /jobs should return 403 without API key."""
        response = client.post("/jobs/example", json={"message": "test"})
        assert response.status_code == 403

    def test_post_job_rejects_invalid_api_key(self, client):
        """POST /jobs should return 401 with invalid API key."""
        response = client.post(
            "/jobs/example",
            json={"message": "test"},
            headers={"X-API-Key": "invalid-key"},
        )
        assert response.status_code == 401

    def test_post_job_accepts_valid_api_key(self, client):
        """POST /jobs should return 200 with valid API key."""
        response = client.post(
            "/jobs/example",
            json={"message": "test"},
            headers={"X-API-Key": "test-api-key"},
        )
        assert response.status_code == 200

    def test_get_job_requires_api_key(self, client):
        """GET /jobs/{id} should return 403 without API key."""
        response = client.get("/jobs/123")
        assert response.status_code == 403

    def test_get_job_accepts_valid_api_key(self, client):
        """GET /jobs/{id} should return 200 with valid API key."""
        response = client.get("/jobs/123", headers={"X-API-Key": "test-api-key"})
        assert response.status_code == 200
