"""
Health-check route.

Provides a lightweight endpoint that monitoring tools, load balancers,
or CI pipelines can hit to verify the application is running.

Endpoint:
    GET /health  →  {"status": "ok"}
"""

from fastapi import APIRouter

from app.schemas.health import HealthResponse

router = APIRouter(tags=["Infrastructure"])


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Application health check",
)
def health_check() -> HealthResponse:
    """Return a simple status payload confirming the server is alive."""
    return HealthResponse(status="ok")
