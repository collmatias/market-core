"""
Order and OrderItem models — marketplace order system between vets and suppliers.

Order state machine:
  DRAFT → PLACED → QUOTED → ACCEPTED → SHIPPED → DELIVERED
                                    ↘ CANCELLED (from any state except DELIVERED)
"""
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Text, Enum,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import enum

from core.database import Base


class OrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PLACED = "PLACED"
    QUOTED = "QUOTED"
    ACCEPTED = "ACCEPTED"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


# Valid transitions: current_status → [allowed_next_statuses]
ORDER_TRANSITIONS = {
    OrderStatus.DRAFT: [OrderStatus.PLACED, OrderStatus.CANCELLED],
    OrderStatus.PLACED: [OrderStatus.QUOTED, OrderStatus.CANCELLED],
    OrderStatus.QUOTED: [OrderStatus.ACCEPTED, OrderStatus.PLACED, OrderStatus.CANCELLED],
    OrderStatus.ACCEPTED: [OrderStatus.SHIPPED, OrderStatus.CANCELLED],
    OrderStatus.SHIPPED: [OrderStatus.DELIVERED, OrderStatus.CANCELLED],
    OrderStatus.DELIVERED: [],
    OrderStatus.CANCELLED: [],
}


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, autoincrement=True)
    buyer_tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    supplier_tenant_id = Column(Integer, ForeignKey("tenants.id"), nullable=False, index=True)
    status = Column(Enum(OrderStatus), nullable=False, default=OrderStatus.DRAFT)
    total = Column(Numeric(12, 2), default=0)
    notes = Column(Text, nullable=True)
    quoted_total = Column(Numeric(12, 2), nullable=True)
    supplier_notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    buyer = relationship("Tenant", foreign_keys=[buyer_tenant_id], backref="orders_placed")
    supplier = relationship("Tenant", foreign_keys=[supplier_tenant_id], backref="orders_received")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    supplier_product_id = Column(Integer, ForeignKey("supplier_products.id"), nullable=True)
    description = Column(String(300), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    quoted_price = Column(Numeric(10, 2), nullable=True)

    order = relationship("Order", back_populates="items")
    supplier_product = relationship("SupplierProduct")
