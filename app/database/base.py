"""
SQLAlchemy declarative Base.

All ORM model classes must inherit from `Base` so that
`Base.metadata.create_all(...)` can discover and create their tables.

Kept in its own module to avoid circular imports: models import Base,
and engine.py imports Base.metadata — neither needs to import the other.
"""

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """
    Shared declarative base for every SQLAlchemy model in Morpheus.

    Extend this class when defining new tables.  Example:

        class JournalEntry(Base):
            __tablename__ = "journal_entries"
            id = mapped_column(Integer, primary_key=True)
            ...
    """

    pass
