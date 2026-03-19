"""
MasterProduct model — central product catalog for barcode lookup.

Populated from public APIs (Open Food Facts, etc.) and manual entries.
"""
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Index
from sqlalchemy.sql import func

from core.database import Base


class MasterProduct(Base):
    __tablename__ = "master_products"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ean = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(String(300), nullable=False)
    brand = Column(String(150), nullable=True)
    category = Column(String(100), nullable=True)
    suggested_price = Column(Numeric(10, 2), nullable=True)
    image_url = Column(Text, nullable=True)
    source = Column(String(50), default="manual")  # manual, openfoodfacts, upc_db
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    __table_args__ = (
        Index("ix_master_products_description_trgm", "description"),
    )
