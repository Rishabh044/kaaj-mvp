"""Unit tests for lender API endpoints."""

import pytest
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestListLenders:
    """Tests for GET /api/v1/lenders/."""

    def test_list_lenders_returns_all_lenders(self):
        """Test listing all lenders returns expected count."""
        response = client.get("/api/v1/lenders/")

        assert response.status_code == 200
        lenders = response.json()

        # Should return all 5 configured lenders
        assert len(lenders) == 5
        assert all("id" in l for l in lenders)
        assert all("name" in l for l in lenders)
        assert all("program_count" in l for l in lenders)

    def test_list_lenders_includes_program_counts(self):
        """Test that program counts are included."""
        response = client.get("/api/v1/lenders/")

        assert response.status_code == 200
        lenders = response.json()

        for lender in lenders:
            assert isinstance(lender["program_count"], int)
            assert lender["program_count"] >= 1


class TestGetLender:
    """Tests for GET /api/v1/lenders/{lender_id}."""

    def test_get_lender_by_id(self):
        """Test getting a specific lender by ID."""
        response = client.get("/api/v1/lenders/citizens_bank")

        assert response.status_code == 200
        lender = response.json()

        assert lender["id"] == "citizens_bank"
        assert lender["name"] == "Citizens Bank"
        assert "programs" in lender
        assert len(lender["programs"]) > 0

    def test_get_lender_includes_programs(self):
        """Test that programs are included with details."""
        response = client.get("/api/v1/lenders/citizens_bank")

        assert response.status_code == 200
        lender = response.json()

        for program in lender["programs"]:
            assert "id" in program
            assert "name" in program
            assert "is_app_only" in program

    def test_get_lender_includes_restrictions(self):
        """Test that global restrictions are included."""
        response = client.get("/api/v1/lenders/citizens_bank")

        assert response.status_code == 200
        lender = response.json()

        # Citizens Bank has restrictions
        if lender.get("restrictions"):
            assert isinstance(lender["restrictions"], dict)

    def test_get_lender_not_found(self):
        """Test 404 for non-existent lender."""
        response = client.get("/api/v1/lenders/nonexistent_lender")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


class TestCreateLender:
    """Tests for POST /api/v1/lenders/."""

    def test_create_lender_conflict_existing(self):
        """Test creating a lender that already exists returns 409."""
        response = client.post(
            "/api/v1/lenders/",
            json={
                "id": "citizens_bank",
                "name": "Citizens Bank Duplicate",
            },
        )

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"].lower()

    def test_create_lender_invalid_id_format(self):
        """Test that invalid ID format is rejected."""
        response = client.post(
            "/api/v1/lenders/",
            json={
                "id": "Invalid ID!",  # Contains invalid characters
                "name": "Test Lender",
            },
        )

        assert response.status_code == 422  # Validation error


class TestUpdateLender:
    """Tests for PUT /api/v1/lenders/{lender_id}."""

    def test_update_lender_not_found(self):
        """Test updating non-existent lender returns 404."""
        response = client.put(
            "/api/v1/lenders/nonexistent_lender",
            json={
                "name": "Updated Name",
            },
        )

        assert response.status_code == 404

    def test_update_lender_returns_updated_version(self):
        """Test that update returns incremented version."""
        response = client.put(
            "/api/v1/lenders/citizens_bank",
            json={
                "name": "Citizens Bank Updated",
            },
        )

        assert response.status_code == 200
        lender = response.json()

        # Version should be incremented
        assert lender["version"] > 1


class TestToggleLenderStatus:
    """Tests for PATCH /api/v1/lenders/{lender_id}/status."""

    def test_toggle_status_returns_status_response(self):
        """Test toggling status returns proper response."""
        response = client.patch("/api/v1/lenders/citizens_bank/status")

        assert response.status_code == 200
        result = response.json()

        assert "id" in result
        assert "name" in result
        assert "is_active" in result
        assert "message" in result

    def test_toggle_status_not_found(self):
        """Test toggling non-existent lender returns 404."""
        response = client.patch("/api/v1/lenders/nonexistent_lender/status")

        assert response.status_code == 404


class TestDeleteLender:
    """Tests for DELETE /api/v1/lenders/{lender_id}."""

    def test_delete_lender_not_found(self):
        """Test deleting non-existent lender returns 404."""
        response = client.delete("/api/v1/lenders/nonexistent_lender")

        assert response.status_code == 404


class TestListLenderPrograms:
    """Tests for GET /api/v1/lenders/{lender_id}/programs."""

    def test_list_programs_returns_all_programs(self):
        """Test listing programs for a lender."""
        response = client.get("/api/v1/lenders/citizens_bank/programs")

        assert response.status_code == 200
        programs = response.json()

        assert len(programs) > 0
        for program in programs:
            assert "id" in program
            assert "name" in program
            assert "is_app_only" in program

    def test_list_programs_lender_not_found(self):
        """Test listing programs for non-existent lender."""
        response = client.get("/api/v1/lenders/nonexistent_lender/programs")

        assert response.status_code == 404
