"""
Sync API route module.

Exposes POST /sync endpoint to receive logs captured on the mobile PWA,
commits them as raw logs, and runs the classification pipeline.
"""

import logging
from datetime import datetime, date
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.database.engine import get_db
from app.services import log_service
from app.services.classification_service import get_classification_service

logger = logging.getLogger(__name__)

router = APIRouter(tags=["sync"])


class MobileLog(BaseModel):
    id: str
    text: str
    created_at: str  # ISO 8601 string (e.g. 2026-06-21T10:15:30.000Z)


class SyncPayload(BaseModel):
    logs: list[MobileLog]


@router.post("/sync", summary="Sync mobile logs to laptop")
def sync_logs(payload: SyncPayload, db: Session = Depends(get_db)):
    """
    Sync logs captured on the mobile companion application.
    For each log:
      1. Store raw log in database under the correct date.
      2. Classify raw log using active LLM (OpenRouter / Gemini).
      3. Save structured LogEntry and Activity records.
    """
    classifier = get_classification_service()
    received_count = 0

    for m_log in payload.logs:
        text_str = m_log.text.strip()
        if not text_str:
            continue

        # Parse date from ISO string; fallback to today's date on parse error
        try:
            # Handle standard Javascript ISO format ending in Z
            iso_str = m_log.created_at.replace("Z", "+00:00")
            dt = datetime.fromisoformat(iso_str)
            log_date = dt.date()
        except Exception:
            logger.warning("Failed to parse log created_at: %s, falling back to today", m_log.created_at)
            log_date = date.today()

        logger.info("Syncing raw log: '%s' for date: %s", text_str[:30], log_date)

        # 1. Store raw log
        raw_log = log_service.create_raw_log(db, content=text_str, entry_date=log_date)

        # 2. Run LLM classifier
        try:
            classified_items = classifier.classify(text_str, db)
        except Exception:
            logger.exception("Failed to classify synced log: '%s'", text_str)
            classified_items = []

        # 3. Store structured entries and activities
        for item in classified_items:
            ref_id = log_service.resolve_reference_id(db, item.entry_type, item.reference_name)
            if ref_id is not None:
                # Merge activities into notes for backwards compatibility
                notes = ", ".join(item.activities) if item.activities else None
                log_entry = log_service.create_structured_entry(
                    db,
                    entry_type=item.entry_type,
                    reference_id=ref_id,
                    status=item.status,
                    content=notes,
                    entry_date=log_date,
                    raw_log_id=raw_log.id,
                )

                # Store granular parsed activities
                for act_name in item.activities:
                    log_service.create_activity(db, log_entry_id=log_entry.id, name=act_name)

        received_count += 1

    return {"success": True, "received": received_count}
