"""
Review payload builder.

Pure functions that convert a ReviewResult dataclass into a
structured dictionary suitable for sending to any LLM provider.

This module is provider-agnostic — it knows about ReviewResult
but nothing about Gemini, OpenAI, etc.
"""

from app.services.review_service import ReviewResult


def to_llm_payload(
    review_type: str,
    review_key: str,
    result: ReviewResult,
) -> dict:
    """
    Convert a ReviewResult into a structured dict for LLM analysis.

    The output is a clean, self-contained JSON-serialisable dict
    that any LLM provider can consume.

    Args:
        review_type: "daily", "weekly", or "monthly"
        review_key:  Date-based key (e.g., "2026-06-19", "2026-W25")
        result:      Populated ReviewResult from ReviewService

    Returns:
        Dict ready to be JSON-serialised and included in an LLM prompt.
    """
    # ── Schedule entries ──────────────────────────────────────────
    schedule_items = []
    for sr in result.schedule_reviews:
        item: dict = {
            "name": sr.block.name,
            "time_range": f"{sr.block.start_time} – {sr.block.end_time}",
        }

        if result.is_single_day:
            # Daily: include status and notes
            item["status"] = sr.status or "not_logged"
            if sr.content:
                item["notes"] = sr.content
        else:
            # Range (weekly/monthly): include aggregated counts
            item["completed"] = sr.completed_count
            item["partial"] = sr.partial_count
            item["missed"] = sr.missed_count
            item["total_logged"] = sr.total_logged

        schedule_items.append(item)

    # ── Rule entries ──────────────────────────────────────────────
    rule_items = []
    for rr in result.rule_reviews:
        item = {
            "name": rr.rule.name,
        }

        if result.is_single_day:
            item["status"] = rr.status or "not_logged"
            if rr.content:
                item["notes"] = rr.content
        else:
            item["followed"] = rr.followed_count
            item["violated"] = rr.violated_count
            item["total_logged"] = rr.total_logged

        rule_items.append(item)

    # ── Statistics ────────────────────────────────────────────────
    stats = {
        "schedule": {
            "total_logged": result.schedule_stats.total_logged,
            "completed": result.schedule_stats.completed,
            "partial": result.schedule_stats.partial,
            "missed": result.schedule_stats.missed,
        },
        "rules": {
            "total_logged": result.rule_stats.total_logged,
            "followed": result.rule_stats.followed,
            "violated": result.rule_stats.violated,
        },
    }

    return {
        "review_type": review_type,
        "review_key": review_key,
        "date_range": {
            "start": str(result.start_date),
            "end": str(result.end_date),
        },
        "schedule": schedule_items,
        "rules": rule_items,
        "statistics": stats,
    }
