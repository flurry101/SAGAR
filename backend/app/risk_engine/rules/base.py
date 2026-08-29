"""Abstract BaseRule interface for Risk Engine safety rules."""

from abc import ABC, abstractmethod
from app.risk_engine.schemas import RiskInput, RuleResult


class BaseRule(ABC):
    """Abstract base class for all deterministic safety rules in the Risk Engine."""

    @property
    @abstractmethod
    def rule_id(self) -> str:
        """Unique identifier for the rule."""
        pass

    @property
    @abstractmethod
    def rule_name(self) -> str:
        """Human-readable display name for the rule."""
        pass

    @abstractmethod
    def applies(self, risk_input: RiskInput) -> bool:
        """
        Check if this rule is applicable to the provided risk input.
        Must be pure and deterministic.
        """
        pass

    @abstractmethod
    def evaluate(self, risk_input: RiskInput) -> RuleResult:
        """
        Evaluate the safety rule against the risk input.
        Must be pure and deterministic: same input -> same output.
        If required input data is missing, must return a RuleResult with
        status=INSUFFICIENT_INFORMATION rather than guessing or crashing.
        """
        pass
