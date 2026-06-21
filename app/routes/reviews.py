"""
Review page routes.

Server-rendered pages for daily, weekly, and monthly reviews.

Endpoints:
    GET /review/daily              → Daily review form (default: today)
    GET /review/daily?date=...     → Daily review for a specific date
    GET /review/weekly             → Weekly review (default: current week)
    GET /review/weekly?start=...   → Weekly review for a specific week
    GET /review/monthly            → Monthly review (default: current month)
    GET /review/monthly?year=&month= → Monthly review for a specific month
"""

from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import schedule_service, rule_service, review_service
from app.services import ai_summary_service

router = APIRouter(prefix="/review", tags=["Reviews"])

_settings = get_settings()


# --------------------------------------------------------------------------- #
#  Helper: shared context for all review pages                                 #
# --------------------------------------------------------------------------- #

def _base_context(request: Request, db: Session) -> dict:
    """Build sidebar context shared by every page."""
    return {
        "request": request,
        "app_name": _settings.APP_NAME,
        "app_version": _settings.APP_VERSION,
        "schedule_blocks": schedule_service.get_all_blocks(db),
        "rules": rule_service.get_all_rules(db),
    }


def _render(request: Request, template: str, context: dict) -> HTMLResponse:
    """Shorthand for TemplateResponse."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
    )


# --------------------------------------------------------------------------- #
#  GET /review/daily  — Daily review page                                      #
# --------------------------------------------------------------------------- #

@router.get("/daily", response_class=HTMLResponse, summary="Daily review")
def daily_review_page(
    request: Request,
    date: date | None = Query(None, alias="date"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Render the daily review for a given date.

    If no date is supplied, defaults to today.
    """
    target_date = date or __import__("datetime").date.today()
    result = review_service.daily_review(db, target_date)

    # AI summary (cached or freshly generated; None if unavailable)
    ai_summary = ai_summary_service.get_or_generate_summary(
        db,
        review_type="daily",
        review_key=str(target_date),
        review_result=result,
    )

    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "reviews",
        "active_id": "daily",
        "review": result,
        "target_date": target_date,
        "today": __import__("datetime").date.today(),
        "ai_summary": ai_summary,
    })
    return _render(request, "review_daily.html", ctx)


# --------------------------------------------------------------------------- #
#  GET /review/weekly  — Weekly review page                                    #
# --------------------------------------------------------------------------- #

@router.get("/weekly", response_class=HTMLResponse, summary="Weekly review")
def weekly_review_page(
    request: Request,
    start: date | None = Query(None, alias="start"),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Render the weekly review.

    If no start date is supplied, defaults to the Monday of the
    current week.  The user can navigate between weeks.
    """
    today = __import__("datetime").date.today()
    week_start = start or review_service.get_current_week_start(today)
    # Snap to Monday in case user provides a non-Monday date
    week_start = week_start - timedelta(days=week_start.weekday())
    week_end = week_start + timedelta(days=6)

    result = review_service.weekly_review(db, week_start)

    # Compute prev/next week for navigation
    prev_week = week_start - timedelta(days=7)
    next_week = week_start + timedelta(days=7)

    # AI summary — weekly key uses ISO week format (e.g., "2026-W25")
    iso_year, iso_week, _ = week_start.isocalendar()
    weekly_key = f"{iso_year}-W{iso_week:02d}"
    ai_summary = ai_summary_service.get_or_generate_summary(
        db,
        review_type="weekly",
        review_key=weekly_key,
        review_result=result,
    )

    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "reviews",
        "active_id": "weekly",
        "review": result,
        "week_start": week_start,
        "week_end": week_end,
        "prev_week": prev_week,
        "next_week": next_week,
        "today": today,
        # Total days in the week for percentage calculations
        "total_days": 7,
        "ai_summary": ai_summary,
    })
    return _render(request, "review_weekly.html", ctx)


# --------------------------------------------------------------------------- #
#  GET /review/monthly  — Monthly review page                                  #
# --------------------------------------------------------------------------- #

@router.get("/monthly", response_class=HTMLResponse, summary="Monthly review")
def monthly_review_page(
    request: Request,
    year: int | None = Query(None),
    month: int | None = Query(None),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """
    Render the monthly review.

    If no year/month is supplied, defaults to the current month.
    The user can navigate between months.
    """
    import calendar
    import datetime as _dt

    today = _dt.date.today()
    target_year = year or today.year
    target_month = month or today.month

    # Clamp month to valid range
    if target_month < 1:
        target_month = 12
        target_year -= 1
    elif target_month > 12:
        target_month = 1
        target_year += 1

    result = review_service.monthly_review(db, target_year, target_month)

    # AI summary — monthly key uses "YYYY-MM" format
    monthly_key = f"{target_year}-{target_month:02d}"
    ai_summary = ai_summary_service.get_or_generate_summary(
        db,
        review_type="monthly",
        review_key=monthly_key,
        review_result=result,
    )

    # Month name for display
    month_name = calendar.month_name[target_month]
    days_in_month = calendar.monthrange(target_year, target_month)[1]

    # Compute prev/next month
    if target_month == 1:
        prev_year, prev_month = target_year - 1, 12
    else:
        prev_year, prev_month = target_year, target_month - 1

    if target_month == 12:
        next_year, next_month = target_year + 1, 1
    else:
        next_year, next_month = target_year, target_month + 1

    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "reviews",
        "active_id": "monthly",
        "review": result,
        "target_year": target_year,
        "target_month": target_month,
        "month_name": month_name,
        "days_in_month": days_in_month,
        "prev_year": prev_year,
        "prev_month": prev_month,
        "next_year": next_year,
        "next_month": next_month,
        "today": today,
        "ai_summary": ai_summary,
    })
    return _render(request, "review_monthly.html", ctx)
