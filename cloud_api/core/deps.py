"""
Shared FastAPI dependencies.
"""
from core.database import get_db  # noqa: F401 — re-export for convenience
from core.auth import require_admin  # noqa: F401
