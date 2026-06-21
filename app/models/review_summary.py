"""
ReviewSummary ORM model.

Stores cached AI-generated review summaries so the LLM is only
called once per review period.  Subsequent visits return the cached
version from SQLite.

Cache key: (review_type, review_key) — unique constraint.
"""

from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class ReviewSummary(Base):
    """
    Cached AI review summary.

    Attributes:
        review_type:  "daily", "weekly", or "monthly"
        review_key:   Date-based key:
                        daily   → "2026-06-19"
                        weekly  → "2026-W25"
                        monthly → "2026-06"
        summary_json: Full JSON string of the AI analysis.
        created_at:   Timestamp when the summary was generated.
    """

    __tablename__ = "review_summaries"

    __table_args__ = (
        UniqueConstraint(
            "review_type",
            "review_key",
            name="uq_review_type_key",
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    review_type: Mapped[str] = mapped_column(String(10), nullable=False)
    review_key: Mapped[str] = mapped_column(String(20), nullable=False)
    summary_json: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, nullable=False
    )

    def __repr__(self) -> str:
        return (
            f"<ReviewSummary(type={self.review_type!r}, "
            f"key={self.review_key!r})>"
        )
