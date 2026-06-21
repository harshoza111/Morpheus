"""
Log entry service — CRUD operations.

Handles creating, reading, and querying log entries.
This is the most active service: every form submission flows through here.
"""

from datetime import date

from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry
from app.models.raw_log import RawLog
from app.models.activity import Activity
from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule
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


def create_raw_log(db: Session, content: str, entry_date: date) -> RawLog:
    """Insert a new raw natural language log."""
    raw_log = RawLog(content=content, entry_date=entry_date)
    db.add(raw_log)
    db.commit()
    db.refresh(raw_log)
    return raw_log


def resolve_reference_id(db: Session, entry_type: str, reference_name: str) -> int | None:
    """
    Look up the primary key ID of a ScheduleBlock or Rule by its name.
    Does case-insensitive matching.
    """
    name_clean = reference_name.strip().lower()
    if entry_type == "schedule":
        block = (
            db.query(ScheduleBlock)
            .filter(ScheduleBlock.name.ilike(name_clean))
            .first()
        )
        return block.id if block else None
    elif entry_type == "rule":
        rule = (
            db.query(Rule)
            .filter(Rule.name.ilike(name_clean))
            .first()
        )
        return rule.id if rule else None
    return None


def create_structured_entry(
    db: Session,
    entry_type: str,
    reference_id: int,
    status: str,
    content: str | None,
    entry_date: date,
    raw_log_id: int,
) -> LogEntry:
    """Insert a classified structured log entry linked back to its raw log."""
    entry = LogEntry(
        entry_type=entry_type,
        reference_id=reference_id,
        status=status,
        content=content,
        entry_date=entry_date,
        raw_log_id=raw_log_id,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return entry


def create_activity(db: Session, log_entry_id: int, name: str) -> Activity:
    """Store an individual activity parsed from the raw log."""
    activity = Activity(log_entry_id=log_entry_id, name=name)
    db.add(activity)
    db.commit()
    db.refresh(activity)
    return activity

