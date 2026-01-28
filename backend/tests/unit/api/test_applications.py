"""Unit tests for application API endpoints."""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


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

    def test_submit_application_success(self, valid_application):
        """Test successful application submission."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "running"
            mock_run.run_id = "test-run-123"
            mock_trigger.return_value = mock_run

            response = client.post("/api/v1/applications/", json=valid_application)

            assert response.status_code == 201
            result = response.json()

            assert "id" in result
            assert "application_number" in result
            assert result["status"] == "processing"
            assert result["workflow_run_id"] == "test-run-123"

    def test_submit_application_generates_unique_id(self, valid_application):
        """Test that unique IDs are generated."""
        with patch("app.api.routes.applications.trigger_evaluation") as mock_trigger:
            mock_run = MagicMock()
            mock_run.status = "running"
            mock_run.run_id = "test-run-123"
            mock_trigger.return_value = mock_run

            response1 = client.post("/api/v1/applications/", json=valid_application)
            response2 = client.post("/api/v1/applications/", json=valid_application)

            assert response1.json()["id"] != response2.json()["id"]
            assert response1.json()["application_number"] != response2.json()["application_number"]

    def test_submit_application_invalid_fico_score(self):
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

        response = client.post("/api/v1/applications/", json=invalid_app)

        assert response.status_code == 422

    def test_submit_application_missing_required_fields(self):
        """Test validation rejects missing required fields."""
        incomplete_app = {
            "applicant": {
                "fico_score": 720,
            },
            # Missing business, equipment, loan_request
        }

        response = client.post("/api/v1/applications/", json=incomplete_app)

        assert response.status_code == 422


class TestListApplications:
    """Tests for GET /api/v1/applications/."""

    def test_list_applications_returns_paginated(self):
        """Test that applications are returned with pagination."""
        response = client.get("/api/v1/applications/")

        assert response.status_code == 200
        result = response.json()

        assert "items" in result
        assert "total" in result
        assert "skip" in result
        assert "limit" in result

    def test_list_applications_pagination_params(self):
        """Test pagination parameters are respected."""
        response = client.get("/api/v1/applications/?skip=10&limit=50")

        assert response.status_code == 200
        result = response.json()

        assert result["skip"] == 10
        assert result["limit"] == 50


class TestGetApplication:
    """Tests for GET /api/v1/applications/{application_id}."""

    def test_get_application_not_found(self):
        """Test getting non-existent application returns 404."""
        response = client.get("/api/v1/applications/00000000-0000-0000-0000-000000000000")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestGetApplicationStatus:
    """Tests for GET /api/v1/applications/{application_id}/status."""

    def test_get_status_returns_completed(self):
        """Test getting status returns completed status.

        Note: Currently returns 'completed' as a stub for the demo frontend.
        In production, this would query the actual workflow/database status.
        """
        response = client.get("/api/v1/applications/test-123/status")

        assert response.status_code == 200
        result = response.json()

        assert result["application_id"] == "test-123"
        assert result["status"] == "completed"


class TestGetMatchResults:
    """Tests for GET /api/v1/applications/{application_id}/results."""

    def test_get_results_returns_matches(self):
        """Test getting results returns matching results."""
        response = client.get("/api/v1/applications/test-123/results")

        assert response.status_code == 200
        result = response.json()

        assert result["application_id"] == "test-123"
        assert "total_evaluated" in result
        assert "total_eligible" in result
        assert "matches" in result

    def test_get_results_includes_criteria_breakdown(self):
        """Test that results include criteria breakdown."""
        response = client.get("/api/v1/applications/test-123/results")

        assert response.status_code == 200
        result = response.json()

        # Each match should have criteria details
        for match in result["matches"]:
            assert "lender_id" in match
            assert "lender_name" in match
            assert "is_eligible" in match
            assert "fit_score" in match

    def test_get_results_ranks_eligible_lenders(self):
        """Test that eligible lenders have ranks."""
        response = client.get("/api/v1/applications/test-123/results")

        assert response.status_code == 200
        result = response.json()

        # Eligible lenders should have ranks
        eligible = [m for m in result["matches"] if m["is_eligible"]]
        if eligible:
            assert all(m.get("rank") is not None for m in eligible)
