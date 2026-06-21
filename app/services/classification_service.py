"""
ClassificationService — local Llama 3.2 natural language log classification pipeline.

Loads and runs local Llama 3.2 3B model for journal analysis and
category mapping.
"""

from abc import ABC, abstractmethod
import json
import logging
from typing import List

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule

logger = logging.getLogger(__name__)


# ─── Pydantic Schemas ─────────────────────────────────────────────

class ClassifiedEntry(BaseModel):
    """A structured log entry outputted by the classification pipeline."""
    entry_type: str            # "schedule" or "rule"
    reference_name: str        # e.g., "Morning Study" or "Exercise Mandatory"
    status: str                # "completed"/"partial"/"missed" (schedule) or "followed"/"violated" (rule)
    activities: List[str] = [] # e.g., ["Leetcode", "CLRS"]
    confidence: float = 1.0


# ─── Classification Interface ─────────────────────────────────────

class ClassificationService(ABC):
    """Abstract Base Class for raw log classifiers."""

    @abstractmethod
    def classify(self, raw_log: str, db: Session) -> List[ClassifiedEntry]:
        """
        Analyze a raw text log and return structured classifications.

        Args:
            raw_log: The natural language string submitted by the user.
            db:      Active database session for fetching block/rule names.

        Returns:
            List of ClassifiedEntry objects.
        """
        pass


# ─── LLM Classifier Delegation ─────────────────────────────────────

class LLMClassificationService(ClassificationService):
    """
    Classification service that delegates log parsing to the active
    LLMProvider (either OpenRouter or Gemini).
    """

    def classify(self, raw_log: str, db: Session) -> List[ClassifiedEntry]:
        from app.services.llm import get_llm_provider
        provider = get_llm_provider()
        if not provider:
            logger.warning("No LLM provider configured — classification skipped")
            return []

        # Get list of blocks & rules to construct prompt dynamic context
        blocks = [b.name for b in db.query(ScheduleBlock).all()]
        rules = [r.name for r in db.query(Rule).all()]

        results = provider.classify_log(raw_log, blocks, rules)
        if not results:
            return []

        classified_entries = []
        for item in results:
            try:
                entry = ClassifiedEntry(
                    entry_type=item.get("entry_type", ""),
                    reference_name=item.get("reference_name", ""),
                    status=item.get("status", ""),
                    activities=item.get("activities", []) or [],
                    confidence=float(item.get("confidence", 1.0))
                )
                classified_entries.append(entry)
            except Exception:
                logger.exception("Failed to parse classified entry: %s", item)

        return classified_entries


# ─── Service Provider Factory ─────────────────────────────────────

_classification_service_instance = None

def get_classification_service() -> ClassificationService:
    """Resolve the ClassificationService singleton, pointing to LLMClassificationService."""
    global _classification_service_instance
    if _classification_service_instance is not None:
        return _classification_service_instance

    _classification_service_instance = LLMClassificationService()
    return _classification_service_instance

