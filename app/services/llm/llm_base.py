"""
LLM provider abstract base class.

Defines the contract that any LLM backend must implement.
Switching from Gemini to OpenAI, Ollama, etc. requires only
implementing this interface and updating the factory in __init__.py.
"""

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Every provider must implement `analyze_review`, which receives
    a structured review payload (plain dict) and returns a structured
    analysis dict — or None on any failure.

    Providers are responsible for:
      - Building the prompt from the payload
      - Calling the LLM API
      - Parsing the response into the expected schema
      - Catching and logging all errors

    Providers must NEVER:
      - Access the database
      - Import ORM models
      - Raise exceptions to the caller
    """

    @abstractmethod
    def analyze_review(self, payload: dict) -> dict | None:
        """
        Analyze structured review data and return a summary.

        Args:
            payload: Structured dict with review_type, date_range,
                     schedule entries, rule entries, and statistics.

        Returns:
            Dict with keys: overall_assessment, successes,
            missed_opportunities, patterns, recommendations.
            Returns None on any failure.
        """
        ...

    @abstractmethod
    def classify_log(
        self,
        raw_log: str,
        blocks: list[str],
        rules: list[str],
    ) -> list[dict] | None:
        """
        Classify a raw natural language log into structured entries.

        Args:
            raw_log: The raw text string submitted by the user.
            blocks:  List of available schedule block names.
            rules:   List of active compliance rule names.

        Returns:
            A list of dicts, where each dict matches the structured schema:
              - "entry_type": "schedule" or "rule"
              - "reference_name": Exact block or rule name
              - "status": "completed"/"partial"/"missed" or "followed"/"violated"
              - "activities": List of matching task strings
              - "confidence": Float between 0.0 and 1.0
            Returns None on failure.
        """
        ...
