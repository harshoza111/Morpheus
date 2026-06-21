"""
ORM models package.

Import every model here so that `Base.metadata` discovers all tables
before `init_db()` calls `create_all()`.
"""

from app.models.schedule_block import ScheduleBlock  # noqa: F401
from app.models.rule import Rule  # noqa: F401
from app.models.log_entry import LogEntry  # noqa: F401
from app.models.review_summary import ReviewSummary  # noqa: F401
from app.models.raw_log import RawLog  # noqa: F401
from app.models.activity import Activity  # noqa: F401

