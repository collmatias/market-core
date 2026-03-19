"""
License model — tracks desktop license activations.
"""
from sqlalchemy import Column, String, Date, Boolean, DateTime, Text
from sqlalchemy.sql import func

from core.database import Base


class License(Base):
    __tablename__ = "licenses"

    hardware_id = Column(String, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    client_email = Column(String(255), nullable=True)
    company_name = Column(String(200), nullable=True)
    company_email = Column(String(255), nullable=True)
    company_tax_id = Column(String(30), nullable=True)
    plan = Column(String(20), default="MONTHLY", nullable=False)
    expiration_date = Column(Date, nullable=True)  # NULL = perpetual
    is_active = Column(Boolean, default=True, nullable=False)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
