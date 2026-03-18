"""
Backward-compatibility shim — imports from the new location.
"""
from core.database import engine, SessionLocal, Base, get_db  # noqa: F401
