"""
SQLAlchemy engine and session management.

Responsibilities:
  1. Create the SQLAlchemy `Engine` bound to the configured DATABASE_URL.
  2. Provide a `SessionLocal` factory for creating scoped sessions.
  3. Expose `get_db()` — a FastAPI dependency that yields a session and
     ensures it is closed after the request.
  4. Expose `init_db()` — called once at application startup to create
     all tables that don't already exist.
"""

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import get_settings
from app.database.base import Base

# --------------------------------------------------------------------------- #
#  Engine & session factory                                                    #
# --------------------------------------------------------------------------- #

_settings = get_settings()

engine = create_engine(
    _settings.DATABASE_URL,
    # `check_same_thread=False` is required for SQLite when used with
    # FastAPI's threaded request handling.
    connect_args={"check_same_thread": False},
    echo=_settings.DEBUG,  # log SQL statements when DEBUG=True
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


# --------------------------------------------------------------------------- #
#  FastAPI dependency                                                          #
# --------------------------------------------------------------------------- #


def get_db() -> Generator[Session, None, None]:
    """
    Yield a database session for the duration of a single request.

    Usage in a route:

        @router.get("/items")
        def list_items(db: Session = Depends(get_db)):
            ...

    The session is automatically closed when the request finishes,
    even if an exception occurs.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# --------------------------------------------------------------------------- #
#  Table creation                                                              #
# --------------------------------------------------------------------------- #


def init_db() -> None:
    """
    Create all tables registered on `Base.metadata`.

    This is safe to call repeatedly — SQLAlchemy's `create_all` is a
    no-op for tables that already exist.

    NOTE: For production systems with schema migrations, replace this
    with Alembic.  During early development, `create_all` is sufficient.
    """
    Base.metadata.create_all(bind=engine)
