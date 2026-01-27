"""Policy loader for reading and validating lender YAML configurations."""

import logging
from pathlib import Path
from typing import Optional

import yaml
from pydantic import ValidationError

from app.policies.schema import LenderPolicy

logger = logging.getLogger(__name__)


class PolicyLoadError(Exception):
    """Raised when a policy cannot be loaded or validated."""

    def __init__(self, lender_id: str, message: str, details: Optional[dict] = None):
        self.lender_id = lender_id
        self.message = message
        self.details = details or {}
        super().__init__(f"Failed to load policy '{lender_id}': {message}")


class PolicyLoader:
    """Loads and caches lender policy configurations from YAML files."""

    def __init__(self, policies_dir: Optional[Path] = None):
        """Initialize the policy loader.

        Args:
            policies_dir: Directory containing lender YAML files.
                         Defaults to app/policies/lenders/.
        """
        if policies_dir is None:
            policies_dir = Path(__file__).parent / "lenders"
        self.policies_dir = Path(policies_dir)
        self._cache: dict[str, LenderPolicy] = {}
        self._load_errors: dict[str, PolicyLoadError] = {}

    def load_policy(self, lender_id: str, use_cache: bool = True) -> LenderPolicy:
        """Load and validate a single lender policy.

        Args:
            lender_id: The lender identifier (filename without .yaml extension)
            use_cache: Whether to use cached policy if available

        Returns:
            Validated LenderPolicy object

        Raises:
            PolicyLoadError: If the policy file doesn't exist or is invalid
        """
        # Check cache first
        if use_cache and lender_id in self._cache:
            return self._cache[lender_id]

        # Check if we've already tried and failed to load this policy
        if lender_id in self._load_errors:
            raise self._load_errors[lender_id]

        policy_path = self.policies_dir / f"{lender_id}.yaml"

        # Check file exists
        if not policy_path.exists():
            error = PolicyLoadError(
                lender_id,
                f"Policy file not found: {policy_path}",
                {"path": str(policy_path)},
            )
            self._load_errors[lender_id] = error
            raise error

        # Load YAML
        try:
            with open(policy_path, "r", encoding="utf-8") as f:
                raw_data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            error = PolicyLoadError(
                lender_id,
                f"Invalid YAML syntax: {e}",
                {"yaml_error": str(e)},
            )
            self._load_errors[lender_id] = error
            raise error

        if raw_data is None:
            error = PolicyLoadError(
                lender_id,
                "Policy file is empty",
            )
            self._load_errors[lender_id] = error
            raise error

        # Validate with Pydantic
        try:
            policy = LenderPolicy(**raw_data)
        except ValidationError as e:
            error = PolicyLoadError(
                lender_id,
                f"Schema validation failed: {e.error_count()} errors",
                {"validation_errors": e.errors()},
            )
            self._load_errors[lender_id] = error
            raise error

        # Verify ID matches filename
        if policy.id != lender_id:
            error = PolicyLoadError(
                lender_id,
                f"Policy ID '{policy.id}' does not match filename '{lender_id}'",
                {"policy_id": policy.id, "expected_id": lender_id},
            )
            self._load_errors[lender_id] = error
            raise error

        # Cache and return
        self._cache[lender_id] = policy
        logger.info(f"Loaded policy: {lender_id} (version {policy.version})")
        return policy

    def get_all_lender_ids(self) -> list[str]:
        """Get list of all available lender IDs.

        Returns:
            List of lender IDs (YAML filenames without extension)
        """
        if not self.policies_dir.exists():
            return []

        return [
            f.stem
            for f in self.policies_dir.glob("*.yaml")
            if not f.stem.startswith("_")  # Skip template files
        ]

    def load_all_policies(self, skip_errors: bool = False) -> list[LenderPolicy]:
        """Load all available lender policies.

        Args:
            skip_errors: If True, skip policies that fail to load.
                        If False, raise on first error.

        Returns:
            List of validated LenderPolicy objects

        Raises:
            PolicyLoadError: If skip_errors is False and any policy fails to load
        """
        policies = []
        lender_ids = self.get_all_lender_ids()

        for lender_id in lender_ids:
            try:
                policy = self.load_policy(lender_id)
                policies.append(policy)
            except PolicyLoadError as e:
                if skip_errors:
                    logger.warning(f"Skipping invalid policy: {e}")
                else:
                    raise

        return policies

    def get_active_policies(self) -> list[LenderPolicy]:
        """Load all policies (alias for load_all_policies with skip_errors=True).

        Returns:
            List of successfully loaded LenderPolicy objects
        """
        return self.load_all_policies(skip_errors=True)

    def reload(self) -> None:
        """Clear the cache and reload all policies."""
        self._cache.clear()
        self._load_errors.clear()
        logger.info("Policy cache cleared")

    def is_cached(self, lender_id: str) -> bool:
        """Check if a policy is currently cached.

        Args:
            lender_id: The lender identifier

        Returns:
            True if the policy is in the cache
        """
        return lender_id in self._cache

    def get_cached_policy(self, lender_id: str) -> Optional[LenderPolicy]:
        """Get a policy from cache without loading.

        Args:
            lender_id: The lender identifier

        Returns:
            The cached policy or None if not cached
        """
        return self._cache.get(lender_id)

    def invalidate(self, lender_id: str) -> None:
        """Remove a specific policy from the cache.

        Args:
            lender_id: The lender identifier to invalidate
        """
        self._cache.pop(lender_id, None)
        self._load_errors.pop(lender_id, None)
        logger.debug(f"Invalidated cache for: {lender_id}")
