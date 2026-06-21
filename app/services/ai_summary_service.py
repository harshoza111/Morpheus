"""
AI summary service — orchestration between cache, payload, and LLM.

This is the single entry-point that routes call to get an AI summary.
It handles:
  1. Checking the DB cache (review_summaries table)
  2. Building the LLM payload from ReviewResult
  3. Calling the LLM provider
  4. Saving the result to the cache
  5. Returning the summary dict (or None on failure)

This module never calls the LLM API directly — it delegates to
whatever LLMProvider is configured via the factory.
"""

import json
import logging

from sqlalchemy.orm import Session

from app.models.review_summary import ReviewSummary
from app.services.llm import get_llm_provider
from app.services.review_payload_builder import to_llm_payload
from app.services.review_service import ReviewResult

logger = logging.getLogger(__name__)


def get_or_generate_summary(
    db: Session,
    review_type: str,
    review_key: str,
    review_result: ReviewResult,
) -> dict | None:
    """
    Get a cached AI summary or generate a new one.

    Args:
        db:            Active database session.
        review_type:   "daily", "weekly", or "monthly".
        review_key:    Date-based key (e.g., "2026-06-19").
        review_result: Populated ReviewResult from ReviewService.

    Returns:
        Dict with keys: overall_assessment, successes,
        missed_opportunities, patterns, recommendations.
        Returns None if AI is unavailable or the call fails.
    """
    # ── 1. Check cache ────────────────────────────────────────────
    cached = (
        db.query(ReviewSummary)
        .filter(
            ReviewSummary.review_type == review_type,
            ReviewSummary.review_key == review_key,
        )
        .first()
    )

    if cached:
        logger.info(
            "AI summary cache hit: %s/%s", review_type, review_key
        )
        try:
            return json.loads(cached.summary_json)
        except (json.JSONDecodeError, TypeError):
            logger.warning("Corrupted cache entry — regenerating")
            db.delete(cached)
            db.commit()

    # ── 2. Check if LLM is available ─────────────────────────────
    provider = get_llm_provider()
    if provider is None:
        logger.info("No LLM provider configured — skipping AI summary")
        return None

    # ── 3. Skip if no data to analyze ─────────────────────────────
    total = (
        review_result.schedule_stats.total_logged
        + review_result.rule_stats.total_logged
    )
    if total == 0:
        logger.info("No log data for %s/%s — skipping AI summary", review_type, review_key)
        return None

    # ── 4. Build payload and call LLM ─────────────────────────────
    payload = to_llm_payload(review_type, review_key, review_result)
    logger.info("Calling LLM for %s/%s", review_type, review_key)

    summary = provider.analyze_review(payload)

    if summary is None:
        logger.warning("LLM returned None for %s/%s", review_type, review_key)
        return None

    # ── 5. Save to cache ──────────────────────────────────────────
    try:
        row = ReviewSummary(
            review_type=review_type,
            review_key=review_key,
            summary_json=json.dumps(summary, ensure_ascii=False),
        )
        db.add(row)
        db.commit()
        logger.info("AI summary cached: %s/%s", review_type, review_key)
    except Exception:
        logger.exception("Failed to cache AI summary")
        db.rollback()
        # Still return the summary even if caching failed

    return summary
