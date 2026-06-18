"""
Log entry service — CRUD operations.

Handles creating, reading, and querying log entries.
This is the most active service: every form submission flows through here.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry
from app.schemas.log_entry import LogEntryCreate


def create_log_entry(db: Session, payload: LogEntryCreate) -> LogEntry:
    """
    Insert a new log entry and return the created row.

    The caller (route) is responsible for building the LogEntryCreate
    from form data.
    """
    entry = LogEntry(
        entry_type=payload.entry_type,
        reference_id=payload.reference_id,
        status=payload.status,
        content=payload.content or None,
        entry_date=payload.entry_date,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def get_entries_for_date(
    db: Session,
    target_date: date,
    entry_type: str | None = None,
) -> list[LogEntry]:
    """
    Return all log entries for a given date, optionally filtered by type.

    Args:
        target_date: The calendar date to query.
        entry_type:  "schedule", "rule", or None for all types.
    """
    query = db.query(LogEntry).filter(LogEntry.entry_date == target_date)
    if entry_type:
        query = query.filter(LogEntry.entry_type == entry_type)
    return query.order_by(LogEntry.created_at.desc()).all()


def get_recent_entries(db: Session, limit: int = 15) -> list[LogEntry]:
    """Return the N most recent log entries across all types."""
    return (
        db.query(LogEntry)
        .order_by(LogEntry.created_at.desc())
        .limit(limit)
        .all()
    )


def count_entries_for_date(
    db: Session,
    target_date: date,
    entry_type: str,
) -> int:
    """Count how many log entries exist for a given date and type."""
    return (
        db.query(LogEntry)
        .filter(LogEntry.entry_date == target_date)
        .filter(LogEntry.entry_type == entry_type)
        .count()
    )
