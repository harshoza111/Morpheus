"""
Rule service — CRUD operations.

Encapsulates all database interactions for rules.
Routes call these functions; they should never build queries directly.
"""

from sqlalchemy.orm import Session

from app.models.rule import Rule


def get_all_rules(db: Session) -> list[Rule]:
    """Return all rules ordered by their sort_order."""
    return db.query(Rule).order_by(Rule.sort_order).all()


def get_rule_by_id(db: Session, rule_id: int) -> Rule | None:
    """Return a single rule by primary key, or None."""
    return db.query(Rule).filter(Rule.id == rule_id).first()
