"""
API and page routes package.

Each module in this package defines an `APIRouter` that is registered
with the main FastAPI application in `app.main`.

Convention:
  - `health.py`  → operational / infrastructure endpoints
  - `pages.py`   → server-rendered HTML pages (Jinja2)
  - Future files  → feature-specific API routes (e.g., `journal.py`)
"""
