"""
LogEntry ORM model.

The central logging table.  Each row records the user's compliance
with either a schedule block or a rule for a given date.

Fields:
  - entry_type:   "schedule" or "rule"
  - reference_id: FK-like pointer to schedule_blocks.id or rules.id
  - status:       schedule → completed/partial/missed
                  rule     → followed/violated
  - content:      optional freeform notes
  - entry_date:   the calendar date being logged (may differ from created_at)
  - created_at:   timestamp when the row was inserted
"""

from datetime import date, datetime

from sqlalchemy import Date, DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class LogEntry(Base):
    """A single compliance log against a schedule block or rule."""

    __tablename__ = "log_entries"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # "schedule" or "rule"
    entry_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Points to schedule_blocks.id or rules.id depending on entry_type
    reference_id: Mapped[int] = mapped_column(Integer, nullable=False)

    # Schedule: completed | partial | missed
    # Rule:     followed  | violated
    status: Mapped[str] = mapped_column(String(20), nullable=False)

    # Optional freeform notes / journal content
    content: Mapped[str | None] = mapped_column(Text, nullable=True)

    # The calendar date this log relates to (e.g. "today")
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)

    # Row creation timestamp (auto-set by the database)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return (
            f"<LogEntry {self.entry_type}:{self.reference_id} "
            f"status={self.status} date={self.entry_date}>"
        )
