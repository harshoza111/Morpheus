"""
Business-logic services package.

Services encapsulate domain logic and orchestrate interactions between
the database layer (models) and external integrations.

Routes should be thin — they validate input, call a service, and
return the result.  Heavy logic belongs here.

Available services:
  - schedule_service:        CRUD for schedule blocks
  - rule_service:            CRUD for rules
  - log_service:             CRUD for log entries
  - review_service:          Daily / weekly / monthly review aggregation
  - review_payload_builder:  ReviewResult → structured dict for LLM
  - ai_summary_service:      Cache + LLM orchestration
"""

from app.services import schedule_service  # noqa: F401
from app.services import rule_service  # noqa: F401
from app.services import log_service  # noqa: F401
from app.services import review_service  # noqa: F401
from app.services import review_payload_builder  # noqa: F401
from app.services import ai_summary_service  # noqa: F401
from app.services import classification_service  # noqa: F401
from app.services import statistics_service  # noqa: F401

