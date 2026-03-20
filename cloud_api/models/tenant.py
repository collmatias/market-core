"""
Tenant model — represents a registered organization (retail store, wholesale, or both).
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import enum

from core.database import Base


class TenantType(str, enum.Enum):
    RETAIL = "RETAIL"
    WHOLESALE = "WHOLESALE"
    BOTH = "BOTH"


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    type = Column(Enum(TenantType), nullable=False, default=TenantType.RETAIL)
    tax_id = Column(String(30), unique=True, nullable=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    phone = Column(String(50), nullable=True)
    address = Column(String(300), nullable=True)
    region = Column(String(100), nullable=True)  # e.g. "AR-CBA" (country-province)
    plan = Column(String(30), default="FREE", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
