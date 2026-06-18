"""
Schedule block service — CRUD operations.

Encapsulates all database interactions for schedule blocks.
Routes call these functions; they should never build queries directly.
"""

from sqlalchemy.orm import Session

from app.models.schedule_block import ScheduleBlock


def get_all_blocks(db: Session) -> list[ScheduleBlock]:
    """Return all schedule blocks ordered by their sort_order."""
    return db.query(ScheduleBlock).order_by(ScheduleBlock.sort_order).all()


def get_block_by_id(db: Session, block_id: int) -> ScheduleBlock | None:
    """Return a single schedule block by primary key, or None."""
    return db.query(ScheduleBlock).filter(ScheduleBlock.id == block_id).first()
