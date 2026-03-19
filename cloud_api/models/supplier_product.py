"""
SupplierProduct model — products listed by suppliers in the marketplace.
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, Boolean, DateTime, Text,
    ForeignKey, Index,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from core.database import Base


class SupplierProduct(Base):
    __tablename__ = "supplier_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    master_product_id = Column(Integer, ForeignKey("master_products.id"), nullable=True)
    sku = Column(String(50), nullable=True)
    ean = Column(String(50), nullable=True, index=True)
    description = Column(String(300), nullable=False)
    brand = Column(String(150), nullable=True)
    category = Column(String(100), nullable=True)
    unit_price = Column(Numeric(10, 2), nullable=False)
    stock_available = Column(Integer, default=0)
    is_active = Column(Boolean, default=True, nullable=False)
    image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    tenant = relationship("Tenant", backref="products")
    master_product = relationship("MasterProduct")

    __table_args__ = (
        Index("ix_supplier_products_tenant_sku", "tenant_id", "sku", unique=True),
    )
