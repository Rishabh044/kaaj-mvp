"""Rule registry for automatic rule discovery and management."""

from typing import Type

from app.rules.base import Rule


class RuleRegistry:
    """Registry for managing rule implementations.

    The registry pattern allows rules to be registered with a decorator
    and then looked up by their type identifier at runtime.
    """

    _rules: dict[str, Type[Rule]] = {}
    _instances: dict[str, Rule] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a rule class.

        Usage:
            @RuleRegistry.register("credit_score")
            class CreditScoreRule(Rule):
                ...

        Args:
            name: The type identifier for this rule.

        Returns:
            Decorator function that registers the rule class.
        """

        def decorator(rule_class: Type[Rule]) -> Type[Rule]:
            if not issubclass(rule_class, Rule):
                raise TypeError(f"{rule_class.__name__} must be a subclass of Rule")
            cls._rules[name] = rule_class
            return rule_class

        return decorator

    @classmethod
    def get_rule(cls, name: str) -> Rule:
        """Get a rule instance by name.

        Instances are cached to avoid creating multiple instances
        of the same rule.

        Args:
            name: The type identifier of the rule.

        Returns:
            An instance of the rule.

        Raises:
            KeyError: If no rule is registered with the given name.
        """
        if name not in cls._rules:
            raise KeyError(f"No rule registered with name: {name}")

        if name not in cls._instances:
            cls._instances[name] = cls._rules[name]()

        return cls._instances[name]

    @classmethod
    def get_rule_class(cls, name: str) -> Type[Rule]:
        """Get the rule class by name.

        Args:
            name: The type identifier of the rule.

        Returns:
            The rule class.

        Raises:
            KeyError: If no rule is registered with the given name.
        """
        if name not in cls._rules:
            raise KeyError(f"No rule registered with name: {name}")
        return cls._rules[name]

    @classmethod
    def has_rule(cls, name: str) -> bool:
        """Check if a rule is registered with the given name.

        Args:
            name: The type identifier to check.

        Returns:
            True if a rule is registered, False otherwise.
        """
        return name in cls._rules

    @classmethod
    def list_rules(cls) -> list[str]:
        """List all registered rule names.

        Returns:
            List of registered rule type identifiers.
        """
        return list(cls._rules.keys())

    @classmethod
    def clear(cls) -> None:
        """Clear all registered rules.

        Primarily used for testing.
        """
        cls._rules.clear()
        cls._instances.clear()


# Convenience function
def get_rule(name: str) -> Rule:
    """Get a rule instance by name.

    This is a convenience function that delegates to RuleRegistry.get_rule.

    Args:
        name: The type identifier of the rule.

    Returns:
        An instance of the rule.
    """
    return RuleRegistry.get_rule(name)
