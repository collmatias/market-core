"""
License model — tracks desktop license activations.
"""
from sqlalchemy import Column, String, Date, Boolean, DateTime
from sqlalchemy.sql import func

from core.database import Base


class License(Base):
    __tablename__ = "licenses"

    hardware_id = Column(String, primary_key=True, index=True)
    client_name = Column(String, nullable=False)
    expiration_date = Column(Date, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
