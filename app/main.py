"""
Morpheus — FastAPI application factory.

This is the single entry-point that assembles every component:
  - Loads configuration from .env / environment
  - Initialises the database (creates tables on first run)
  - Seeds default schedule blocks and rules
  - Mounts static files and Jinja2 templates
  - Registers all route modules

Run the server with:
    uvicorn app.main:app --reload
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.config import get_settings
from app.database import init_db, seed_defaults
from app.database.engine import SessionLocal
from app.routes import health, pages

# Ensure all ORM models are imported so Base.metadata knows about them
import app.models  # noqa: F401

# --------------------------------------------------------------------------- #
#  Path constants                                                              #
# --------------------------------------------------------------------------- #

_APP_DIR = Path(__file__).resolve().parent
_TEMPLATES_DIR = _APP_DIR / "templates"
_STATIC_DIR = _APP_DIR / "static"


# --------------------------------------------------------------------------- #
#  Application lifespan (startup / shutdown hooks)                             #
# --------------------------------------------------------------------------- #


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the server starts and once when it shuts down.

    Startup:
      1. Create all database tables (idempotent).
      2. Seed default schedule blocks and rules (idempotent).
      3. Attach Jinja2 template engine to app.state.

    Shutdown:
      (Reserved for future cleanup.)
    """
    # ---- Startup ---------------------------------------------------------- #
    init_db()

    # Seed default data using a one-off session
    db = SessionLocal()
    try:
        seed_defaults(db)
    finally:
        db.close()

    app.state.templates = Jinja2Templates(directory=str(_TEMPLATES_DIR))
    yield
    # ---- Shutdown --------------------------------------------------------- #


# --------------------------------------------------------------------------- #
#  Application instance                                                        #
# --------------------------------------------------------------------------- #

settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Personal life-tracking application for schedule & rule compliance.",
    lifespan=lifespan,
)

# --------------------------------------------------------------------------- #
#  Static files                                                                #
# --------------------------------------------------------------------------- #

app.mount(
    "/static",
    StaticFiles(directory=str(_STATIC_DIR)),
    name="static",
)

# --------------------------------------------------------------------------- #
#  Route registration                                                          #
# --------------------------------------------------------------------------- #

app.include_router(health.router)
app.include_router(pages.router)
