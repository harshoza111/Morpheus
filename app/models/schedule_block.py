"""
ScheduleBlock ORM model.

Represents a fixed time-slot in the user's daily schedule.
Each block has a name, start time, and end time.  The user logs
activity against these blocks to track schedule compliance.

Example blocks: "Sleep", "Jogging", "Deep Work", etc.
"""

from sqlalchemy import Integer, String, Time
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ScheduleBlock(Base):
    """A named time window in the user's daily schedule."""

    __tablename__ = "schedule_blocks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)  # "HH:MM" 24h
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)    # "HH:MM" 24h
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<ScheduleBlock {self.name} ({self.start_time}–{self.end_time})>"
