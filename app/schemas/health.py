"""
Health-check response schema.

Provides a typed contract for the GET /health endpoint so that
clients and documentation (Swagger UI) know exactly what to expect.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response body for the health-check endpoint."""

    status: str = "ok"
