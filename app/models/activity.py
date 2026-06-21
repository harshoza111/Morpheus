"""
Activity ORM model.

Stores individual activities classified from a raw log.
Linked to a structured LogEntry.
"""

from sqlalchemy import Integer, String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class Activity(Base):
    """An individual activity name mapped to a log entry."""

    __tablename__ = "activities"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    log_entry_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("log_entries.id", ondelete="CASCADE"),
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship back to LogEntry
    log_entry = relationship("LogEntry", back_populates="activities_list")

    def __repr__(self) -> str:
        return f"<Activity id={self.id} name={self.name!r}>"
