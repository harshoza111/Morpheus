"""
Server-rendered page routes (Jinja2 templates) for Morpheus.

Endpoints:
    GET  /             → Minimalist logging quick-capture page
    POST /log          → Submit raw natural language log, run classifier, store entries
    GET  /schedule     → Read-only schedule blocks list
    GET  /rules        → Read-only compliance rules list
    GET  /statistics   → Statistics & recent logging dashboard
"""

from datetime import date

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import get_db
from app.services import schedule_service, rule_service, log_service

router = APIRouter(tags=["Pages"])

_settings = get_settings()


# --------------------------------------------------------------------------- #
#  Helper: build shared template context (sidebar data)                        #
# --------------------------------------------------------------------------- #

def _base_context(request: Request, db: Session) -> dict:
    """
    Build the context dict shared by every page: sidebar navigation links,
    collapsible sidebar state, and app metadata.
    """
    return {
        "request": request,
        "app_name": _settings.APP_NAME,
        "app_version": _settings.APP_VERSION,
        "schedule_blocks": schedule_service.get_all_blocks(db),
        "rules": rule_service.get_all_rules(db),
    }


def _render(request: Request, template: str, context: dict) -> HTMLResponse:
    """Shorthand for TemplateResponse with request context."""
    return request.app.state.templates.TemplateResponse(
        request=request,
        name=template,
        context=context,
    )


# --------------------------------------------------------------------------- #
#  GET /  — Minimalist Logging Homepage                                        #
# --------------------------------------------------------------------------- #

@router.get("/", response_class=HTMLResponse, summary="Home Quick Capture")
def homepage(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Render the simple text capture box for daily logging."""
    ctx = _base_context(request, db)
    ctx.update({
        "today": date.today(),
        "active_page": "home",
    })
    return _render(request, "index.html", ctx)


# --------------------------------------------------------------------------- #
#  POST /log — Submit raw log & execute classification pipeline                #
# --------------------------------------------------------------------------- #

@router.post("/log", summary="Submit raw text log")
def submit_raw_log(
    content: str = Form(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    """
    Process raw text log:
      1. Store raw log in DB.
      2. Classify raw log using Local LLM (Llama).
      3. Create structured LogEntry & Activity rows.
      4. Redirect back to Home.
    """
    today = date.today()
    content_str = content.strip()
    
    if content_str:
        # 1. Store raw log
        raw_log = log_service.create_raw_log(db, content=content_str, entry_date=today)
        
        # 2. Run Llama classifier
        from app.services.classification_service import get_classification_service
        classifier = get_classification_service()
        
        classified_items = classifier.classify(content_str, db)
        
        # 3. Store structured entries and activities
        for item in classified_items:
            ref_id = log_service.resolve_reference_id(db, item.entry_type, item.reference_name)
            if ref_id is not None:
                # Merge activities into content note for backwards compatibility
                notes = ", ".join(item.activities) if item.activities else None
                log_entry = log_service.create_structured_entry(
                    db,
                    entry_type=item.entry_type,
                    reference_id=ref_id,
                    status=item.status,
                    content=notes,
                    entry_date=today,
                    raw_log_id=raw_log.id,
                )
                
                # Store granular parsed activities
                for act_name in item.activities:
                    log_service.create_activity(db, log_entry_id=log_entry.id, name=act_name)

    return RedirectResponse(url="/", status_code=303)


# --------------------------------------------------------------------------- #
#  GET /schedule — Read-only schedule list                                     #
# --------------------------------------------------------------------------- #

@router.get("/schedule", response_class=HTMLResponse, summary="Schedule blocks")
def schedule_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Show the list of configured daily schedule blocks."""
    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "schedule",
    })
    return _render(request, "schedule.html", ctx)


# --------------------------------------------------------------------------- #
#  GET /rules — Read-only rules list                                           #
# --------------------------------------------------------------------------- #

@router.get("/rules", response_class=HTMLResponse, summary="Rules list")
def rules_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Show the list of active compliance rules."""
    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "rules",
    })
    return _render(request, "rules.html", ctx)


# --------------------------------------------------------------------------- #
#  GET /statistics — Metrics & Recent Logs Dashboard                           #
# --------------------------------------------------------------------------- #

@router.get("/statistics", response_class=HTMLResponse, summary="Statistics dashboard")
def statistics_page(request: Request, db: Session = Depends(get_db)) -> HTMLResponse:
    """Show overall logging compliance statistics and timeline."""
    from app.services.statistics_service import get_statistics
    
    stats = get_statistics(db)
    ctx = _base_context(request, db)
    ctx.update({
        "active_page": "statistics",
        "stats": stats,
        # Maps for resolving names in template lists
        "block_map": {b.id: b for b in ctx["schedule_blocks"]},
        "rule_map": {r.id: r for r in ctx["rules"]},
    })
    return _render(request, "statistics.html", ctx)
