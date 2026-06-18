"""
Database package.

Provides the SQLAlchemy engine, session factory, and declarative Base
class used by all ORM models.
"""

from app.database.base import Base  # noqa: F401
from app.database.engine import get_db, init_db  # noqa: F401
from app.database.seed import seed_defaults  # noqa: F401
