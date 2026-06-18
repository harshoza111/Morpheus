"""
Pydantic schemas for log entries.

Defines the data shapes for creating and reading log entries.
Kept separate from ORM models so the API contract can evolve
independently of the database schema.
"""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class LogEntryCreate(BaseModel):
    """Payload for creating a new log entry (from form submission)."""
    entry_type: str          # "schedule" or "rule"
    reference_id: int        # FK to schedule_blocks.id or rules.id
    status: str              # schedule: completed/partial/missed, rule: followed/violated
    content: Optional[str] = None
    entry_date: date


class LogEntryRead(BaseModel):
    """Read-only representation of a log entry (for API responses)."""
    id: int
    entry_type: str
    reference_id: int
    status: str
    content: Optional[str]
    entry_date: date
    created_at: datetime

    # Allow reading from ORM objects directly
    model_config = {"from_attributes": True}
