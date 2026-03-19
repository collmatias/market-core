"""
Order router — marketplace order management.

Buyer flow:  create draft → place → accept quote → receive delivery
Supplier flow:  view placed orders → quote → ship → mark delivered
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.deps import get_db
from core.auth import require_tenant_token
from models.order import Order, OrderItem, OrderStatus, ORDER_TRANSITIONS
from models.supplier_product import SupplierProduct
from models.tenant import Tenant, TenantType

router = APIRouter(prefix="/orders", tags=["Orders"])


# --- Schemas ---

class OrderItemCreate(BaseModel):
    supplier_product_id: int | None = None
    description: str
    quantity: int
    unit_price: float


class OrderItemOut(BaseModel):
    id: int
    supplier_product_id: int | None = None
    description: str
    quantity: int
    unit_price: float
    quoted_price: float | None = None

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    supplier_tenant_id: int
    notes: str | None = None
    items: list[OrderItemCreate]


class OrderOut(BaseModel):
    id: int
    buyer_tenant_id: int
    supplier_tenant_id: int
    status: OrderStatus
    total: float
    quoted_total: float | None = None
    notes: str | None = None
    supplier_notes: str | None = None
    items: list[OrderItemOut]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderStatusUpdate(BaseModel):
    status: OrderStatus
    notes: str | None = None
    quoted_total: float | None = None


class OrderQuoteItem(BaseModel):
    item_id: int
    quoted_price: float


class OrderQuote(BaseModel):
    quoted_total: float
    supplier_notes: str | None = None
    items: list[OrderQuoteItem] = []


# --- Buyer endpoints ---

@router.post("/", response_model=OrderOut, status_code=201)
def create_order(
    data: OrderCreate,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Create a new order (buyer → supplier)."""
    # Verify supplier exists and is a supplier
    supplier = db.query(Tenant).filter(Tenant.id == data.supplier_tenant_id).first()
    if not supplier or supplier.type != TenantType.SUPPLIER:
        raise HTTPException(status_code=400, detail="Invalid supplier")

    if not data.items:
        raise HTTPException(status_code=400, detail="Order must have at least one item")

    total = sum(item.quantity * item.unit_price for item in data.items)

    order = Order(
        buyer_tenant_id=tenant.id,
        supplier_tenant_id=data.supplier_tenant_id,
        status=OrderStatus.DRAFT,
        total=total,
        notes=data.notes,
    )
    db.add(order)
    db.flush()

    for item_data in data.items:
        item = OrderItem(
            order_id=order.id,
            supplier_product_id=item_data.supplier_product_id,
            description=item_data.description,
            quantity=item_data.quantity,
            unit_price=item_data.unit_price,
        )
        db.add(item)

    db.commit()
    db.refresh(order)
    return order


@router.get("/my", response_model=list[OrderOut])
def list_my_orders(
    role: str = Query("buyer", regex="^(buyer|supplier)$"),
    status: OrderStatus | None = None,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """List orders. role=buyer shows orders I placed, role=supplier shows orders I received."""
    if role == "buyer":
        query = db.query(Order).filter(Order.buyer_tenant_id == tenant.id)
    else:
        query = db.query(Order).filter(Order.supplier_tenant_id == tenant.id)

    if status:
        query = query.filter(Order.status == status)

    return query.order_by(Order.updated_at.desc()).limit(100).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Get order details (accessible to buyer or supplier)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_tenant_id != tenant.id and order.supplier_tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Access denied")
    return order


# --- Status transitions ---

@router.post("/{order_id}/place", response_model=OrderOut)
def place_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Buyer places the order (DRAFT → PLACED)."""
    order = _get_order_as(db, order_id, tenant.id, role="buyer")
    _transition(order, OrderStatus.PLACED)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/quote", response_model=OrderOut)
def quote_order(
    order_id: int,
    data: OrderQuote,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Supplier quotes the order (PLACED → QUOTED)."""
    order = _get_order_as(db, order_id, tenant.id, role="supplier")
    _transition(order, OrderStatus.QUOTED)
    order.quoted_total = data.quoted_total
    order.supplier_notes = data.supplier_notes

    for qi in data.items:
        item = db.query(OrderItem).filter(
            OrderItem.id == qi.item_id, OrderItem.order_id == order.id
        ).first()
        if item:
            item.quoted_price = qi.quoted_price

    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/accept", response_model=OrderOut)
def accept_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Buyer accepts the quote (QUOTED → ACCEPTED)."""
    order = _get_order_as(db, order_id, tenant.id, role="buyer")
    _transition(order, OrderStatus.ACCEPTED)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/ship", response_model=OrderOut)
def ship_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Supplier marks as shipped (ACCEPTED → SHIPPED)."""
    order = _get_order_as(db, order_id, tenant.id, role="supplier")
    _transition(order, OrderStatus.SHIPPED)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/deliver", response_model=OrderOut)
def deliver_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Buyer confirms delivery (SHIPPED → DELIVERED)."""
    order = _get_order_as(db, order_id, tenant.id, role="buyer")
    _transition(order, OrderStatus.DELIVERED)
    db.commit()
    db.refresh(order)
    return order


@router.post("/{order_id}/cancel", response_model=OrderOut)
def cancel_order(
    order_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Cancel the order (buyer or supplier, from any non-terminal state)."""
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.buyer_tenant_id != tenant.id and order.supplier_tenant_id != tenant.id:
        raise HTTPException(status_code=403, detail="Access denied")
    _transition(order, OrderStatus.CANCELLED)
    db.commit()
    db.refresh(order)
    return order


# --- Helpers ---

def _get_order_as(db: Session, order_id: int, tenant_id: int, role: str) -> Order:
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if role == "buyer" and order.buyer_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not the buyer of this order")
    if role == "supplier" and order.supplier_tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Not the supplier of this order")
    return order


def _transition(order: Order, target: OrderStatus):
    allowed = ORDER_TRANSITIONS.get(order.status, [])
    if target not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {order.status.value} to {target.value}",
        )
    order.status = target
