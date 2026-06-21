"""
RawLog ORM model.

Stores the raw natural language journal/log inputs submitted by the user.
"""

from datetime import date, datetime
from sqlalchemy import Date, DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RawLog(Base):
    """Raw natural language log entry."""

    __tablename__ = "raw_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, nullable=False, server_default=func.now()
    )

    def __repr__(self) -> str:
        return f"<RawLog id={self.id} date={self.entry_date}>"
