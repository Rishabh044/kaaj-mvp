"""Unit tests for application API endpoints."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient


class TestSubmitApplication:
    """Tests for POST /api/v1/applications/."""

    @pytest.fixture
    def valid_application(self):
        """Return a valid application payload."""
        return {
            "applicant": {
                "fico_score": 720,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            "business": {
                "name": "Test Business LLC",
                "state": "TX",
                "years_in_business": 5.0,
            },
            "credit_history": {
                "has_bankruptcy": False,
            },
            "equipment": {
                "category": "construction",
                "year": 2022,
            },
            "loan_request": {
                "amount": 5000000,
                "transaction_type": "purchase",
            },
        }

    @pytest.mark.asyncio
    async def test_submit_application_success(self, client: AsyncClient, valid_application):
        """Test successful application submission."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "running"
            mock_run.run_id = "test-run-123"
            mock_trigger.return_value = mock_run

            response = await client.post("/api/v1/applications/", json=valid_application)

            assert response.status_code == 201
            result = response.json()

            assert "id" in result
            assert "application_number" in result
            assert result["status"] == "processing"
            assert result["workflow_run_id"] == "test-run-123"

    @pytest.mark.asyncio
    async def test_submit_application_generates_unique_id(
        self, client: AsyncClient, valid_application
    ):
        """Test that unique IDs are generated."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "running"
            mock_run.run_id = "test-run-123"
            mock_trigger.return_value = mock_run

            response1 = await client.post("/api/v1/applications/", json=valid_application)
            response2 = await client.post("/api/v1/applications/", json=valid_application)

            assert response1.json()["id"] != response2.json()["id"]
            assert (
                response1.json()["application_number"]
                != response2.json()["application_number"]
            )

    @pytest.mark.asyncio
    async def test_submit_application_invalid_fico_score(self, client: AsyncClient):
        """Test validation rejects invalid FICO score."""
        invalid_app = {
            "applicant": {
                "fico_score": 200,  # Below minimum 300
                "is_homeowner": True,
            },
            "business": {
                "name": "Test Business LLC",
                "state": "TX",
                "years_in_business": 5.0,
            },
            "credit_history": {},
            "equipment": {
                "category": "construction",
                "year": 2022,
            },
            "loan_request": {
                "amount": 5000000,
            },
        }

        response = await client.post("/api/v1/applications/", json=invalid_app)

        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_application_missing_required_fields(self, client: AsyncClient):
        """Test validation rejects missing required fields."""
        incomplete_app = {
            "applicant": {
                "fico_score": 720,
            },
            # Missing business, equipment, loan_request
        }

        response = await client.post("/api/v1/applications/", json=incomplete_app)

        assert response.status_code == 422


class TestListApplications:
    """Tests for GET /api/v1/applications/."""

    @pytest.mark.asyncio
    async def test_list_applications_returns_paginated(self, client: AsyncClient):
        """Test that applications are returned with pagination."""
        response = await client.get("/api/v1/applications/")

        assert response.status_code == 200
        result = response.json()

        assert "items" in result
        assert "total" in result
        assert "skip" in result
        assert "limit" in result

    @pytest.mark.asyncio
    async def test_list_applications_pagination_params(self, client: AsyncClient):
        """Test pagination parameters are respected."""
        response = await client.get("/api/v1/applications/?skip=10&limit=50")

        assert response.status_code == 200
        result = response.json()

        assert result["skip"] == 10
        assert result["limit"] == 50


class TestGetApplication:
    """Tests for GET /api/v1/applications/{application_id}."""

    @pytest.mark.asyncio
    async def test_get_application_not_found(self, client: AsyncClient):
        """Test getting non-existent application returns 404."""
        response = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000"
        )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetApplicationStatus:
    """Tests for GET /api/v1/applications/{application_id}/status."""

    @pytest.mark.asyncio
    async def test_get_status_not_found_for_invalid_uuid(self, client: AsyncClient):
        """Test getting status for non-existent application returns 404."""
        response = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/status"
        )

        assert response.status_code == 404


class TestGetMatchResults:
    """Tests for GET /api/v1/applications/{application_id}/results."""

    @pytest.mark.asyncio
    async def test_get_results_not_found_for_invalid_uuid(self, client: AsyncClient):
        """Test getting results for non-existent application returns 404."""
        response = await client.get(
            "/api/v1/applications/00000000-0000-0000-0000-000000000000/results"
        )

        assert response.status_code == 404


class TestApplicationWorkflow:
    """Integration tests for the full application workflow using database."""

    @pytest.fixture
    def valid_application(self):
        """Return a valid application payload."""
        return {
            "applicant": {
                "fico_score": 720,
                "transunion_score": 715,
                "is_homeowner": True,
                "is_us_citizen": True,
            },
            "business": {
                "name": "Test Trucking LLC",
                "state": "TX",
                "industry_code": "484110",
                "industry_name": "General Freight Trucking",
                "years_in_business": 5.0,
                "annual_revenue": 1500000,
            },
            "credit_history": {
                "has_bankruptcy": False,
                "has_foreclosure": False,
                "has_repossession": False,
            },
            "equipment": {
                "category": "class_8_truck",
                "type": "Sleeper",
                "year": 2022,
                "mileage": 50000,
                "condition": "used",
            },
            "loan_request": {
                "amount": 15000000,
                "requested_term_months": 60,
                "transaction_type": "purchase",
            },
        }

    @pytest.mark.asyncio
    async def test_submit_and_retrieve_application(
        self, client: AsyncClient, valid_application
    ):
        """Test submitting an application and retrieving it."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "completed"
            mock_run.run_id = "test-run-123"
            mock_run.result = {"status": "completed", "ranked_matches": []}
            mock_trigger.return_value = mock_run

            # Submit application
            submit_response = await client.post(
                "/api/v1/applications/", json=valid_application
            )
            assert submit_response.status_code == 201
            app_id = submit_response.json()["id"]

            # Retrieve application
            get_response = await client.get(f"/api/v1/applications/{app_id}")
            assert get_response.status_code == 200

            result = get_response.json()
            assert result["id"] == app_id
            assert result["business_name"] == "Test Trucking LLC"
            assert result["loan_amount"] == 15000000

    @pytest.mark.asyncio
    async def test_submit_and_get_status(self, client: AsyncClient, valid_application):
        """Test submitting an application and checking status."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "completed"
            mock_run.run_id = "test-run-123"
            mock_run.result = {"status": "completed", "ranked_matches": []}
            mock_trigger.return_value = mock_run

            # Submit application
            submit_response = await client.post(
                "/api/v1/applications/", json=valid_application
            )
            assert submit_response.status_code == 201
            app_id = submit_response.json()["id"]

            # Check status
            status_response = await client.get(f"/api/v1/applications/{app_id}/status")
            assert status_response.status_code == 200

            result = status_response.json()
            assert result["application_id"] == app_id
            assert "status" in result

    @pytest.mark.asyncio
    async def test_list_after_submit(self, client: AsyncClient, valid_application):
        """Test that submitted applications appear in the list."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "completed"
            mock_run.run_id = "test-run-123"
            mock_trigger.return_value = mock_run

            # Submit application
            submit_response = await client.post(
                "/api/v1/applications/", json=valid_application
            )
            assert submit_response.status_code == 201
            app_id = submit_response.json()["id"]

            # List applications
            list_response = await client.get("/api/v1/applications/")
            assert list_response.status_code == 200

            result = list_response.json()
            assert result["total"] >= 1
            app_ids = [item["id"] for item in result["items"]]
            assert app_id in app_ids
