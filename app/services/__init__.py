"""
Business-logic services package.

Services encapsulate domain logic and orchestrate interactions between
the database layer (models) and external integrations.

Routes should be thin — they validate input, call a service, and
return the result.  Heavy logic belongs here.

Available services:
  - schedule_service: CRUD for schedule blocks
  - rule_service:     CRUD for rules
  - log_service:      CRUD for log entries
"""

from app.services import schedule_service  # noqa: F401
from app.services import rule_service  # noqa: F401
from app.services import log_service  # noqa: F401
