"""
Server-rendered page routes (Jinja2 templates).

These routes return full HTML pages.  They live separately from pure
API routes so the codebase clearly distinguishes between data endpoints
and rendered views.

Endpoints:
    GET  /                        → Dashboard homepage
    GET  /log/schedule/{id}       → Schedule block logging form
    POST /log/schedule/{id}       → Submit schedule log
    GET  /log/rule/{id}           → Rule logging form
    POST /log/rule/{id}           → Submit rule log
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.models.schedule_block import ScheduleBlock
from app.models.rule import Rule
from app.schemas.log_entry import LogEntryCreate
from app.services import schedule_service, rule_service, log_service

router = APIRouter(tags=["Pages"])

_settings = get_settings()


# --------------------------------------------------------------------------- #
#  Helper: build shared template context (sidebar data)                        #
# --------------------------------------------------------------------------- #

def _base_context(request: Request, db: Session) -> dict:
    """
    Build the context dict shared by every page: sidebar schedule blocks,
    rules, and app metadata.
    """
    return {
        "request": request,  # needed for url_for etc.
        "app_name": _settings.APP_NAME,
        "app_version": _settings.APP_VERSION,
        "schedule_blocks": schedule_service.get_all_blocks(db),
        "rules": rule_service.get_all_rules(db),
    }


def _render(request: Request, template: str, context: dict) -> HTMLResponse:
    """Shorthand for TemplateResponse with request kwarg."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
    )


# --------------------------------------------------------------------------- #
#  GET /  — Dashboard homepage                                                 #
# --------------------------------------------------------------------------- #

@router.get("/", response_class=HTMLResponse, summary="Dashboard")
def homepage(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """
    Render the Morpheus dashboard with today's progress stats and
    recent log entries.
    """
    today = date.today()
    ctx = _base_context(request, db)
    ctx.update({
        "today": today,
        "schedule_count": log_service.count_entries_for_date(db, today, "schedule"),
        "rule_count": log_service.count_entries_for_date(db, today, "rule"),
        "total_blocks": len(ctx["schedule_blocks"]),
        "total_rules": len(ctx["rules"]),
        "recent_entries": log_service.get_recent_entries(db, limit=15),
        # Build lookup dicts so templates can resolve reference_id → name
        "block_map": {b.id: b for b in ctx["schedule_blocks"]},
        "rule_map": {r.id: r for r in ctx["rules"]},
    })
    return _render(request, "index.html", ctx)


# --------------------------------------------------------------------------- #
#  GET / POST  /log/schedule/{block_id}  — Schedule logging form               #
# --------------------------------------------------------------------------- #

@router.get("/log/schedule/{block_id}", response_class=HTMLResponse,
            summary="Schedule log form")
def schedule_log_form(
    request: Request,
    block_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Show the logging form for a specific schedule block."""
    block = schedule_service.get_block_by_id(db, block_id)
    if not block:
        return RedirectResponse(url="/", status_code=303)

    ctx = _base_context(request, db)
    ctx.update({
        "block": block,
        "today": date.today(),
        "saved": False,
    })
    return _render(request, "log_schedule.html", ctx)


@router.post("/log/schedule/{block_id}", response_class=HTMLResponse,
             summary="Submit schedule log")
def schedule_log_submit(
    request: Request,
    block_id: int,
    status: str = Form(...),
    content: str = Form(""),
    entry_date: date = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Process the schedule logging form submission."""
    block = schedule_service.get_block_by_id(db, block_id)
    if not block:
        return RedirectResponse(url="/", status_code=303)

    payload = LogEntryCreate(
        entry_type="schedule",
        reference_id=block_id,
        status=status,
        content=content if content.strip() else None,
        entry_date=entry_date,
    )
    log_service.create_log_entry(db, payload)

    ctx = _base_context(request, db)
    ctx.update({
        "block": block,
        "today": date.today(),
        "saved": True,
    })
    return _render(request, "log_schedule.html", ctx)


# --------------------------------------------------------------------------- #
#  GET / POST  /log/rule/{rule_id}  — Rule logging form                        #
# --------------------------------------------------------------------------- #

@router.get("/log/rule/{rule_id}", response_class=HTMLResponse,
            summary="Rule log form")
def rule_log_form(
    request: Request,
    rule_id: int,
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Show the logging form for a specific rule."""
    rule = rule_service.get_rule_by_id(db, rule_id)
    if not rule:
        return RedirectResponse(url="/", status_code=303)

    ctx = _base_context(request, db)
    ctx.update({
        "rule": rule,
        "today": date.today(),
        "saved": False,
    })
    return _render(request, "log_rule.html", ctx)


@router.post("/log/rule/{rule_id}", response_class=HTMLResponse,
             summary="Submit rule log")
def rule_log_submit(
    request: Request,
    rule_id: int,
    status: str = Form(...),
    content: str = Form(""),
    entry_date: date = Form(...),
    db: Session = Depends(get_db),
) -> HTMLResponse:
    """Process the rule logging form submission."""
    rule = rule_service.get_rule_by_id(db, rule_id)
    if not rule:
        return RedirectResponse(url="/", status_code=303)

    payload = LogEntryCreate(
        entry_type="rule",
        reference_id=rule_id,
        status=status,
        content=content if content.strip() else None,
        entry_date=entry_date,
    )
    log_service.create_log_entry(db, payload)

    ctx = _base_context(request, db)
    ctx.update({
        "rule": rule,
        "today": date.today(),
        "saved": True,
    })
    return _render(request, "log_rule.html", ctx)
