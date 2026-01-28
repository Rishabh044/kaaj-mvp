"""Unit tests for policy loader."""

import tempfile
from pathlib import Path

import pytest
import yaml

from app.policies.loader import PolicyLoader, PolicyLoadError


class TestLoadSinglePolicy:
    """Tests for loading a single policy."""

    def test_load_existing_policy(self, tmp_path):
        """Test loading a valid policy file."""
        # Create a valid policy file
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": 1,
            "programs": [
                {"id": "program_1", "name": "Program 1"},
            ],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        policy = loader.load_policy("test_lender")

        assert policy.id == "test_lender"
        assert policy.name == "Test Lender"
        assert len(policy.programs) == 1

    def test_load_nonexistent_policy(self, tmp_path):
        """Test loading a policy that doesn't exist."""
        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_policy("nonexistent")

        assert "not found" in str(exc_info.value).lower()
        assert exc_info.value.lender_id == "nonexistent"


class TestLoadInvalidPolicy:
    """Tests for loading invalid policies."""

    def test_load_invalid_yaml_syntax(self, tmp_path):
        """Test loading a file with invalid YAML syntax."""
        policy_file = tmp_path / "bad_yaml.yaml"
        with open(policy_file, "w") as f:
            f.write("id: test\n  invalid: yaml: syntax:")

        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_policy("bad_yaml")

        assert "yaml" in str(exc_info.value).lower()

    def test_load_invalid_schema(self, tmp_path):
        """Test loading a file that fails schema validation."""
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": -1,  # Invalid: must be >= 1
            "programs": [],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_policy("test_lender")

        assert "validation" in str(exc_info.value).lower()

    def test_load_empty_file(self, tmp_path):
        """Test loading an empty file."""
        policy_file = tmp_path / "empty.yaml"
        policy_file.touch()

        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_policy("empty")

        assert "empty" in str(exc_info.value).lower()

    def test_load_mismatched_id(self, tmp_path):
        """Test loading a file where ID doesn't match filename."""
        policy_data = {
            "id": "wrong_id",
            "name": "Test Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError) as exc_info:
            loader.load_policy("test_lender")

        assert "does not match" in str(exc_info.value).lower()


class TestPolicyCaching:
    """Tests for policy caching behavior."""

    def test_policy_is_cached(self, tmp_path):
        """Test that loaded policies are cached."""
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)

        # First load
        policy1 = loader.load_policy("test_lender")
        assert loader.is_cached("test_lender")

        # Second load should return cached version
        policy2 = loader.load_policy("test_lender")
        assert policy1 is policy2

    def test_bypass_cache(self, tmp_path):
        """Test loading with cache bypass."""
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        policy1 = loader.load_policy("test_lender")

        # Update the file
        policy_data["version"] = 2
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        # Load with cache bypass
        policy2 = loader.load_policy("test_lender", use_cache=False)

        assert policy1.version == 1
        assert policy2.version == 2

    def test_invalidate_cache(self, tmp_path):
        """Test cache invalidation."""
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        policy_file = tmp_path / "test_lender.yaml"
        with open(policy_file, "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        loader.load_policy("test_lender")
        assert loader.is_cached("test_lender")

        loader.invalidate("test_lender")
        assert not loader.is_cached("test_lender")

    def test_reload_clears_all_cache(self, tmp_path):
        """Test reload clears entire cache."""
        for i in range(3):
            policy_data = {
                "id": f"lender_{i}",
                "name": f"Lender {i}",
                "version": 1,
                "programs": [{"id": "p1", "name": "P1"}],
            }
            policy_file = tmp_path / f"lender_{i}.yaml"
            with open(policy_file, "w") as f:
                yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        for i in range(3):
            loader.load_policy(f"lender_{i}")

        assert all(loader.is_cached(f"lender_{i}") for i in range(3))

        loader.reload()

        assert not any(loader.is_cached(f"lender_{i}") for i in range(3))


class TestGetAllLenders:
    """Tests for getting all lender IDs."""

    def test_get_all_lender_ids(self, tmp_path):
        """Test getting list of all lender IDs."""
        for name in ["lender_a", "lender_b", "lender_c"]:
            policy_file = tmp_path / f"{name}.yaml"
            policy_file.touch()

        loader = PolicyLoader(tmp_path)
        ids = loader.get_all_lender_ids()

        assert set(ids) == {"lender_a", "lender_b", "lender_c"}

    def test_excludes_template_files(self, tmp_path):
        """Test that template files are excluded."""
        (tmp_path / "_template.yaml").touch()
        (tmp_path / "lender_a.yaml").touch()

        loader = PolicyLoader(tmp_path)
        ids = loader.get_all_lender_ids()

        assert "_template" not in ids
        assert "lender_a" in ids

    def test_empty_directory(self, tmp_path):
        """Test getting IDs from empty directory."""
        loader = PolicyLoader(tmp_path)
        ids = loader.get_all_lender_ids()

        assert ids == []


class TestLoadAllPolicies:
    """Tests for loading all policies."""

    def test_load_all_valid_policies(self, tmp_path):
        """Test loading all valid policies."""
        for i, name in enumerate(["lender_a", "lender_b"]):
            policy_data = {
                "id": name,
                "name": f"Lender {name}",
                "version": 1,
                "programs": [{"id": "p1", "name": "P1"}],
            }
            policy_file = tmp_path / f"{name}.yaml"
            with open(policy_file, "w") as f:
                yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        policies = loader.load_all_policies()

        assert len(policies) == 2
        ids = {p.id for p in policies}
        assert ids == {"lender_a", "lender_b"}

    def test_load_all_skip_errors(self, tmp_path):
        """Test loading all policies with skip_errors=True."""
        # Valid policy
        valid_data = {
            "id": "valid_lender",
            "name": "Valid Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        with open(tmp_path / "valid_lender.yaml", "w") as f:
            yaml.dump(valid_data, f)

        # Invalid policy
        with open(tmp_path / "invalid_lender.yaml", "w") as f:
            f.write("invalid: yaml: syntax:")

        loader = PolicyLoader(tmp_path)
        policies = loader.load_all_policies(skip_errors=True)

        assert len(policies) == 1
        assert policies[0].id == "valid_lender"

    def test_load_all_raise_on_error(self, tmp_path):
        """Test loading all policies raises on first error when skip_errors=False."""
        with open(tmp_path / "invalid_lender.yaml", "w") as f:
            f.write("invalid: yaml: syntax:")

        loader = PolicyLoader(tmp_path)

        with pytest.raises(PolicyLoadError):
            loader.load_all_policies(skip_errors=False)


class TestGetActivePolicies:
    """Tests for get_active_policies alias."""

    def test_get_active_policies(self, tmp_path):
        """Test get_active_policies is alias for load_all_policies with skip_errors."""
        # Valid policy
        valid_data = {
            "id": "valid_lender",
            "name": "Valid Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        with open(tmp_path / "valid_lender.yaml", "w") as f:
            yaml.dump(valid_data, f)

        # Invalid policy (should be skipped)
        with open(tmp_path / "invalid_lender.yaml", "w") as f:
            f.write("invalid: yaml:")

        loader = PolicyLoader(tmp_path)
        policies = loader.get_active_policies()

        assert len(policies) == 1
        assert policies[0].id == "valid_lender"


class TestGetCachedPolicy:
    """Tests for get_cached_policy method."""

    def test_get_cached_policy_exists(self, tmp_path):
        """Test getting a cached policy."""
        policy_data = {
            "id": "test_lender",
            "name": "Test Lender",
            "version": 1,
            "programs": [{"id": "p1", "name": "P1"}],
        }
        with open(tmp_path / "test_lender.yaml", "w") as f:
            yaml.dump(policy_data, f)

        loader = PolicyLoader(tmp_path)
        loader.load_policy("test_lender")

        cached = loader.get_cached_policy("test_lender")
        assert cached is not None
        assert cached.id == "test_lender"

    def test_get_cached_policy_not_loaded(self, tmp_path):
        """Test getting a policy that's not cached returns None."""
        loader = PolicyLoader(tmp_path)
        cached = loader.get_cached_policy("nonexistent")
        assert cached is None
