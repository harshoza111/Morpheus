"""
Database seed data.

Populates the schedule_blocks and rules tables with default entries
on first run.  Safe to call repeatedly — skips seeding if data
already exists.
"""

from sqlalchemy.orm import Session

from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule


# --------------------------------------------------------------------------- #
#  Default schedule blocks (ordered by time-of-day)                            #
# --------------------------------------------------------------------------- #

DEFAULT_SCHEDULE_BLOCKS = [
    {"name": "Sleep",                "start_time": "22:00", "end_time": "06:00", "sort_order": 1},
    {"name": "Jogging",              "start_time": "06:00", "end_time": "06:30", "sort_order": 2},
    {"name": "Morning Routine",      "start_time": "06:30", "end_time": "07:00", "sort_order": 3},
    {"name": "Morning Study",        "start_time": "07:00", "end_time": "07:50", "sort_order": 4},
    {"name": "Travel + Breakfast",   "start_time": "07:50", "end_time": "08:45", "sort_order": 5},
    {"name": "Office Morning Study", "start_time": "08:45", "end_time": "10:40", "sort_order": 6},
    {"name": "Deep Work",            "start_time": "10:40", "end_time": "13:00", "sort_order": 7},
    {"name": "Lunch",                "start_time": "13:00", "end_time": "14:00", "sort_order": 8},
    {"name": "Afternoon Work",       "start_time": "14:00", "end_time": "16:30", "sort_order": 9},
    {"name": "Office Evening Study", "start_time": "16:30", "end_time": "17:40", "sort_order": 10},
    {"name": "Travel + Terrace",     "start_time": "17:40", "end_time": "18:45", "sort_order": 11},
    {"name": "Refreshment",          "start_time": "18:45", "end_time": "19:00", "sort_order": 12},
    {"name": "Night Study",          "start_time": "19:00", "end_time": "22:00", "sort_order": 13},
]

# --------------------------------------------------------------------------- #
#  Default rules                                                               #
# --------------------------------------------------------------------------- #

DEFAULT_RULES = [
    {"name": "No Shorts At Home",                  "sort_order": 1},
    {"name": "No Games At Home",                   "sort_order": 2},
    {"name": "Follow Sleep Schedule",              "sort_order": 3},
    {"name": "Exercise Mandatory",                 "sort_order": 4},
    {"name": "Morning Study Must Not Be Wasted",   "sort_order": 5},
    {"name": "Night Study Must Not Be Wasted",     "sort_order": 6},
]


def seed_defaults(db: Session) -> None:
    """
    Insert default schedule blocks and rules if the tables are empty.

    This is called once during application startup (inside the lifespan
    handler).  If rows already exist, no data is modified.
    """
    # -- Schedule blocks ----------------------------------------------------- #
    if db.query(ScheduleBlock).count() == 0:
        for block_data in DEFAULT_SCHEDULE_BLOCKS:
            db.add(ScheduleBlock(**block_data))
        db.commit()

    # -- Rules --------------------------------------------------------------- #
    if db.query(Rule).count() == 0:
        for rule_data in DEFAULT_RULES:
            db.add(Rule(**rule_data))
        db.commit()
