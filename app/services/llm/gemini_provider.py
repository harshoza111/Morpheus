"""
Gemini LLM provider.

Implements LLMProvider using the google-genai SDK (unified SDK).
Uses Gemini 2.0 Flash for fast, structured JSON responses.

This module never touches the database.  It receives a plain dict,
calls the Gemini API, and returns a plain dict (or None on failure).
"""

import json
import logging

from google import genai
from google.genai import types
from pydantic import BaseModel

from app.services.llm.llm_base import LLMProvider

logger = logging.getLogger(__name__)

# ─── Pydantic schema for constrained output ──────────────────────
# Using response_schema guarantees Gemini returns exactly this shape.


class ReviewAnalysis(BaseModel):
    """Schema enforced on the Gemini response."""
    overall_assessment: str
    successes: list[str]
    missed_opportunities: list[str]
    patterns: list[str]
    recommendations: list[str]


class ClassifiedItem(BaseModel):
    """Schema for parsed log item."""
    entry_type: str
    reference_name: str
    status: str
    activities: list[str] = []
    confidence: float = 1.0


class ClassificationResult(BaseModel):
    """Enforces a clean list wrapper on classification output."""
    entries: list[ClassifiedItem]


# ─── System prompt ────────────────────────────────────────────────

_SYSTEM_PROMPT = """\
You are Morpheus, a personal productivity coach who analyzes daily schedule \
and rule compliance data.  You receive structured JSON describing a user's \
logged activities and rule adherence for a specific period.

Your job:
1. Provide a concise overall assessment (2-3 sentences).
2. Identify specific successes worth celebrating.
3. Identify missed opportunities or areas that need attention.
4. Spot behavioral patterns (positive or negative trends).
5. Give actionable, encouraging recommendations.

Rules:
- Be specific — reference actual block names and rule names from the data.
- Be encouraging but honest.
- Keep each bullet point to 1-2 sentences.
- If there is very little data, acknowledge it and focus on what IS logged.
- Never invent data that wasn't provided.
"""


class GeminiProvider(LLMProvider):
    """
    Gemini 2.0 Flash implementation of LLMProvider.

    Uses structured JSON output (response_schema) for guaranteed
    well-formed responses.  All errors are caught and logged —
    the caller receives None on failure.
    """

    MODEL = "gemini-2.0-flash"

    def __init__(self, api_key: str) -> None:
        self._client = genai.Client(api_key=api_key)

    def analyze_review(self, payload: dict) -> dict | None:
        """
        Send the structured review payload to Gemini and parse the
        structured JSON response.

        Returns None on any failure (API error, timeout, bad JSON).
        """
        try:
            user_prompt = (
                "Analyze this review data and provide your assessment:\n\n"
                + json.dumps(payload, indent=2, default=str)
            )

            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=user_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=ReviewAnalysis,
                    temperature=0.7,
                ),
            )

            # response.parsed is a ReviewAnalysis pydantic instance
            if response.parsed:
                return response.parsed.model_dump()

            # Fallback: try parsing response.text as JSON
            if response.text:
                return json.loads(response.text)

            logger.warning("Gemini returned empty response")
            return None

        except Exception:
            logger.exception("Gemini API call failed")
            return None

    def classify_log(
        self,
        raw_log: str,
        blocks: list[str],
        rules: list[str],
    ) -> list[dict] | None:
        """
        Classify a raw log using Gemini's response_schema mode.
        """
        try:
            blocks_str = ", ".join(f"'{b}'" for b in blocks)
            rules_str = ", ".join(f"'{r}'" for r in rules)

            system_prompt = f"""You are Morpheus, an AI that parses natural language logs.
Available Schedule Blocks: [{blocks_str}]
Available Rules: [{rules_str}]

Analyze the user's log. Map events to the available Schedule Blocks and Rules.
Ensure you match exact block/rule names and correct statuses.
"""
            user_content = f"Log: {raw_log}"

            response = self._client.models.generate_content(
                model=self.MODEL,
                contents=user_content,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    response_mime_type="application/json",
                    response_schema=ClassificationResult,
                    temperature=0.1,
                ),
            )

            if response.parsed:
                return [item.model_dump() for item in response.parsed.entries]

            if response.text:
                data = json.loads(response.text)
                if isinstance(data, dict) and "entries" in data:
                    return data["entries"]
                if isinstance(data, list):
                    return data

            logger.warning("Gemini returned empty classification response")
            return None

        except Exception:
            logger.exception("Gemini classify_log call failed")
            return None
