"""
ORM models package.

Import every model here so that `Base.metadata` discovers all tables
before `init_db()` calls `create_all()`.
"""

from app.models.schedule_block import ScheduleBlock  # noqa: F401
from app.models.rule import Rule  # noqa: F401
from app.models.log_entry import LogEntry  # noqa: F401
