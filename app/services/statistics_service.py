"""
StatisticsService — aggregates and queries metrics for the Statistics Dashboard.
"""

from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry
from app.models.raw_log import RawLog


def get_statistics(db: Session) -> dict:
    """
    Calculate and compile all dashboard statistics.

    Args:
        db: Active database session.

    Returns:
        Dict with schedule stats, rule stats, recent raw logs, and structured entries.
    """
    # Schedule log counts
    sched_completed = (
        db.query(LogEntry)
        .filter(LogEntry.entry_type == "schedule", LogEntry.status == "completed")
        .count()
    )
    sched_partial = (
        db.query(LogEntry)
        .filter(LogEntry.entry_type == "schedule", LogEntry.status == "partial")
        .count()
    )
    sched_missed = (
        db.query(LogEntry)
        .filter(LogEntry.entry_type == "schedule", LogEntry.status == "missed")
        .count()
    )

    # Rule compliance counts
    rule_followed = (
        db.query(LogEntry)
        .filter(LogEntry.entry_type == "rule", LogEntry.status == "followed")
        .count()
    )
    rule_violated = (
        db.query(LogEntry)
        .filter(LogEntry.entry_type == "rule", LogEntry.status == "violated")
        .count()
    )

    # Recent raw logs (last 10)
    recent_raw = (
        db.query(RawLog)
        .order_by(RawLog.created_at.desc())
        .limit(10)
        .all()
    )

    # Recent structured log entries (last 15)
    recent_structured = (
        db.query(LogEntry)
        .order_by(LogEntry.created_at.desc())
        .limit(15)
        .all()
    )

    return {
        "schedule": {
            "completed": sched_completed,
            "partial": sched_partial,
            "missed": sched_missed,
            "total": sched_completed + sched_partial + sched_missed,
        },
        "rules": {
            "followed": rule_followed,
            "violated": rule_violated,
            "total": rule_followed + rule_violated,
        },
        "recent_raw": recent_raw,
        "recent_structured": recent_structured,
    }
