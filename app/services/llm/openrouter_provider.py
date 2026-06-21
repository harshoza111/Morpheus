"""
OpenRouter LLM provider.

Implements LLMProvider using the OpenRouter chat completions API.
Supports dynamic model switching and structured JSON outputs.
"""

import json
import logging
import httpx

from app.services.llm.llm_base import LLMProvider

logger = logging.getLogger(__name__)


class OpenRouterProvider(LLMProvider):
    """
    OpenRouter API implementation of LLMProvider.
    Uses httpx for synchronous requests to https://openrouter.ai/api/v1/chat/completions.
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"

    def __init__(self, api_key: str, model: str) -> None:
        self._api_key = api_key
        self._model = model
        self._headers = {
            "Authorization": f"Bearer {self._api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/harshoza111/Morpheus",
            "X-Title": "Morpheus AI Assistant",
        }

    def analyze_review(self, payload: dict) -> dict | None:
        """
        Analyze daily/weekly/monthly review metrics.
        Returns a dictionary matching the ReviewAnalysis schema, or None on failure.
        """
        system_prompt = """You are Morpheus, a productivity coach.
Analyze the user's daily/weekly/monthly logs.
You MUST respond with a valid JSON object matching the following structure:
{
  "overall_assessment": "2-3 sentence general summary of the period",
  "successes": ["success 1", "success 2"],
  "missed_opportunities": ["opportunity 1", "opportunity 2"],
  "patterns": ["pattern 1", "pattern 2"],
  "recommendations": ["recommendation 1", "recommendation 2"]
}
Ensure all keys are present. Keep list items short and action-oriented."""

        user_content = (
            "Analyze this review data and return the JSON assessment:\n\n"
            + json.dumps(payload, indent=2, default=str)
        )

        try:
            body = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.3
            }

            logger.info("Calling OpenRouter (%s) for review analysis...", self._model)
            response = httpx.post(
                self.API_URL,
                headers=self._headers,
                json=body,
                timeout=60.0
            )
            response.raise_for_status()
            
            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"]
            logger.debug("OpenRouter Review Output: %s", content)

            parsed = json.loads(content.strip())
            # Basic validation
            required_keys = ["overall_assessment", "successes", "missed_opportunities", "patterns", "recommendations"]
            if all(k in parsed for k in required_keys):
                return parsed
            
            logger.warning("OpenRouter JSON missing required review keys: %s", parsed)
            return None

        except Exception:
            logger.exception("OpenRouter analyze_review call failed")
            return None

    def classify_log(
        self,
        raw_log: str,
        blocks: list[str],
        rules: list[str],
    ) -> list[dict] | None:
        """
        Parse raw natural language log into schedule/rule mappings.
        Returns a list of classified entries matching the schema, or None on failure.
        """
        blocks_str = ", ".join(f"'{b}'" for b in blocks)
        rules_str = ", ".join(f"'{r}'" for r in rules)

        system_prompt = f"""You are Morpheus, an AI that parses natural language logs.
Available Schedule Blocks: [{blocks_str}]
Available Rules: [{rules_str}]

Analyze the user's log. Map events to the available Schedule Blocks and Rules.
You MUST output a valid JSON object containing a list of entries under the key "entries", structured exactly as:
{{
  "entries": [
    {{
      "entry_type": "schedule" or "rule",
      "reference_name": "Exact block or rule name from the list above",
      "status": "completed"/"partial"/"missed" (for schedule) or "followed"/"violated" (for rule),
      "activities": ["task 1", "task 2"],
      "confidence": 0.0 to 1.0
    }}
  ]
}}

Example Input: I did Jogging and followed sleep schedule.
Example Output:
{{
  "entries": [
    {{"entry_type": "schedule", "reference_name": "Jogging", "status": "completed", "activities": ["Jogging"], "confidence": 0.95}},
    {{"entry_type": "rule", "reference_name": "Follow Sleep Schedule", "status": "followed", "activities": [], "confidence": 1.0}}
  ]
}}"""

        user_content = f"Log: {raw_log}"

        try:
            body = {
                "model": self._model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_content}
                ],
                "response_format": {"type": "json_object"},
                "temperature": 0.1
            }

            logger.info("Calling OpenRouter (%s) for log classification...", self._model)
            response = httpx.post(
                self.API_URL,
                headers=self._headers,
                json=body,
                timeout=30.0
            )
            response.raise_for_status()

            res_data = response.json()
            content = res_data["choices"][0]["message"]["content"]
            logger.debug("OpenRouter Classify Output: %s", content)

            parsed = json.loads(content.strip())
            if "entries" in parsed and isinstance(parsed["entries"], list):
                return parsed["entries"]

            # Fallback if the model returned the array directly in spite of instructions
            if isinstance(parsed, list):
                return parsed

            logger.warning("OpenRouter classification JSON missing 'entries' key: %s", parsed)
            return None

        except Exception:
            logger.exception("OpenRouter classify_log call failed")
            return None
