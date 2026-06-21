"""
Review service — aggregation and querying logic for reviews.

Provides reusable functions for daily, weekly, and (future) monthly
reviews.  All queries filter on `entry_date` (never `created_at`)
because users may log activities after midnight.

Architecture note:
  This service returns plain data structures (dicts / dataclasses).
  A future GeminiReviewService can accept these same structures as
  input to generate AI summaries, without touching any query logic.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta

from sqlalchemy.orm import Session

from app.models.log_entry import LogEntry
from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule


# ═══════════════════════════════════════════════════════════════════
#  Data structures returned by review queries
# ═══════════════════════════════════════════════════════════════════


@dataclass
class ScheduleBlockReview:
    """Review data for a single schedule block."""
    block: ScheduleBlock
    status: str | None = None       # For daily: completed/partial/missed/None
    content: str | None = None      # For daily: freeform notes
    # For range (weekly/monthly) aggregation:
    completed_count: int = 0
    partial_count: int = 0
    missed_count: int = 0
    total_logged: int = 0


@dataclass
class RuleReview:
    """Review data for a single rule."""
    rule: Rule
    status: str | None = None       # For daily: followed/violated/None
    content: str | None = None      # For daily: freeform notes
    # For range aggregation:
    followed_count: int = 0
    violated_count: int = 0
    total_logged: int = 0


@dataclass
class ScheduleStats:
    """Aggregate schedule statistics."""
    total_logged: int = 0
    completed: int = 0
    partial: int = 0
    missed: int = 0


@dataclass
class RuleStats:
    """Aggregate rule statistics."""
    total_logged: int = 0
    followed: int = 0
    violated: int = 0


@dataclass
class ReviewResult:
    """
    Complete review result — used by both daily and weekly reviews.

    A future GeminiReviewService can accept this object directly to
    generate an AI-powered summary without duplicating any query logic.
    """
    start_date: date
    end_date: date
    schedule_reviews: list[ScheduleBlockReview] = field(default_factory=list)
    rule_reviews: list[RuleReview] = field(default_factory=list)
    schedule_stats: ScheduleStats = field(default_factory=ScheduleStats)
    rule_stats: RuleStats = field(default_factory=RuleStats)

    @property
    def is_single_day(self) -> bool:
        return self.start_date == self.end_date


# ═══════════════════════════════════════════════════════════════════
#  Core query: fetch entries for a date range
# ═══════════════════════════════════════════════════════════════════


def _get_entries_in_range(
    db: Session,
    start: date,
    end: date,
    entry_type: str | None = None,
) -> list[LogEntry]:
    """
    Return all log entries whose `entry_date` falls within [start, end].

    This is the single source of truth for date filtering.  Every
    review function calls this — never queries LogEntry directly.
    """
    query = (
        db.query(LogEntry)
        .filter(LogEntry.entry_date >= start)
        .filter(LogEntry.entry_date <= end)
    )
    if entry_type:
        query = query.filter(LogEntry.entry_type == entry_type)
    return query.order_by(LogEntry.entry_date, LogEntry.created_at).all()


# ═══════════════════════════════════════════════════════════════════
#  Build a ReviewResult for any date range (reusable core)
# ═══════════════════════════════════════════════════════════════════


def build_review(
    db: Session,
    start: date,
    end: date,
) -> ReviewResult:
    """
    Build a complete ReviewResult for the given date range.

    Works for daily (start == end), weekly, or monthly reviews.
    This is the single aggregation function — no duplication needed
    for different review periods.

    Args:
        db:    Active database session.
        start: First date to include (inclusive).
        end:   Last date to include (inclusive).

    Returns:
        ReviewResult with per-block, per-rule breakdowns and totals.
    """
    # Fetch all blocks and rules (for showing un-logged items too)
    all_blocks = (
        db.query(ScheduleBlock)
        .order_by(ScheduleBlock.sort_order)
        .all()
    )
    all_rules = (
        db.query(Rule)
        .order_by(Rule.sort_order)
        .all()
    )

    # Fetch entries in the date range
    schedule_entries = _get_entries_in_range(db, start, end, "schedule")
    rule_entries = _get_entries_in_range(db, start, end, "rule")

    is_single_day = (start == end)

    # ── Schedule block reviews ────────────────────────────────────
    schedule_reviews: list[ScheduleBlockReview] = []
    schedule_stats = ScheduleStats()

    # Index entries by reference_id for fast lookup
    sched_by_ref: dict[int, list[LogEntry]] = {}
    for entry in schedule_entries:
        sched_by_ref.setdefault(entry.reference_id, []).append(entry)

    for block in all_blocks:
        entries = sched_by_ref.get(block.id, [])
        review = ScheduleBlockReview(block=block)

        if is_single_day and entries:
            # Daily: take the latest entry for this block
            latest = entries[-1]
            review.status = latest.status
            review.content = latest.content

        # Aggregate counts (works for any range)
        for e in entries:
            review.total_logged += 1
            if e.status == "completed":
                review.completed_count += 1
                schedule_stats.completed += 1
            elif e.status == "partial":
                review.partial_count += 1
                schedule_stats.partial += 1
            elif e.status == "missed":
                review.missed_count += 1
                schedule_stats.missed += 1
            schedule_stats.total_logged += 1

        schedule_reviews.append(review)

    # ── Rule reviews ──────────────────────────────────────────────
    rule_reviews: list[RuleReview] = []
    rule_stats = RuleStats()

    rule_by_ref: dict[int, list[LogEntry]] = {}
    for entry in rule_entries:
        rule_by_ref.setdefault(entry.reference_id, []).append(entry)

    for rule in all_rules:
        entries = rule_by_ref.get(rule.id, [])
        review = RuleReview(rule=rule)

        if is_single_day and entries:
            latest = entries[-1]
            review.status = latest.status
            review.content = latest.content

        for e in entries:
            review.total_logged += 1
            if e.status == "followed":
                review.followed_count += 1
                rule_stats.followed += 1
            elif e.status == "violated":
                review.violated_count += 1
                rule_stats.violated += 1
            rule_stats.total_logged += 1

        rule_reviews.append(review)

    return ReviewResult(
        start_date=start,
        end_date=end,
        schedule_reviews=schedule_reviews,
        rule_reviews=rule_reviews,
        schedule_stats=schedule_stats,
        rule_stats=rule_stats,
    )


# ═══════════════════════════════════════════════════════════════════
#  Convenience wrappers (thin functions calling build_review)
# ═══════════════════════════════════════════════════════════════════


def daily_review(db: Session, target_date: date) -> ReviewResult:
    """Build a review for a single day."""
    return build_review(db, target_date, target_date)


def weekly_review(db: Session, week_start: date) -> ReviewResult:
    """
    Build a review for a 7-day week starting at `week_start`.

    The caller is responsible for computing the correct Monday.
    """
    week_end = week_start + timedelta(days=6)
    return build_review(db, week_start, week_end)


def monthly_review(db: Session, year: int, month: int) -> ReviewResult:
    """
    Build a review for an entire calendar month.

    Not exposed in the UI yet, but the aggregation logic is ready.
    """
    first_day = date(year, month, 1)
    # Last day of month: go to next month, subtract 1 day
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    return build_review(db, first_day, last_day)


def get_current_week_start(target_date: date | None = None) -> date:
    """Return the Monday of the week containing `target_date`."""
    d = target_date or date.today()
    return d - timedelta(days=d.weekday())  # weekday(): Mon=0
