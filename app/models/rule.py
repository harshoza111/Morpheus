"""
Rule ORM model.

Represents a personal rule / discipline commitment the user tracks.
Each day the user can mark a rule as "followed" or "violated" and
optionally add notes.

Example rules: "No Games At Home", "Follow Sleep Schedule", etc.
"""

from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Rule(Base):
    """A personal discipline rule to track compliance against."""

    __tablename__ = "rules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    def __repr__(self) -> str:
        return f"<Rule {self.name}>"
