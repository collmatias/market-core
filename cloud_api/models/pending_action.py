"""
PendingAction model — queued actions for desktop nodes (password resets, etc.).
"""
import secrets
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from sqlalchemy.sql import func

from core.database import Base


class PendingAction(Base):
    __tablename__ = "pending_actions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    hardware_id = Column(String, nullable=False, index=True)
    action_type = Column(String(50), nullable=False)  # FORCE_PASSWORD_RESET, PASSWORD_RESET, etc.
    payload = Column(Text, nullable=True)  # JSON string for extra data
    token = Column(String(64), unique=True, nullable=False, default=lambda: secrets.token_urlsafe(32))
    is_consumed = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
