"""
Pydantic schemas (data-transfer objects) package.

Schemas define the shape of data entering and leaving the API.
They are intentionally separated from ORM models so that the API
contract can evolve independently of the database schema.
"""

from app.schemas.health import HealthResponse  # noqa: F401
from app.schemas.log_entry import LogEntryCreate, LogEntryRead  # noqa: F401
