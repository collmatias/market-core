"""
Supplier router — product listing and marketplace search.

Authenticated endpoints (tenant JWT):
  GET    /supplier/products           — list my products
  POST   /supplier/products           — add product to my catalog
  PATCH  /supplier/products/{id}      — update product
  DELETE /supplier/products/{id}      — deactivate product

Public search (for vets browsing):
  GET /supplier/search?q=&region=     — search supplier products
  GET /supplier/{tenant_id}/products  — list products from a specific supplier
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.deps import get_db
from core.auth import require_tenant_token
from models.supplier_product import SupplierProduct
from models.tenant import Tenant, TenantType

router = APIRouter(prefix="/supplier", tags=["Supplier"])


# --- Schemas ---

class SupplierProductOut(BaseModel):
    id: int
    tenant_id: int
    sku: str | None = None
    ean: str | None = None
    description: str
    brand: str | None = None
    category: str | None = None
    unit_price: float
    stock_available: int
    is_active: bool
    image_url: str | None = None

    class Config:
        from_attributes = True


class SupplierProductCreate(BaseModel):
    sku: str | None = None
    ean: str | None = None
    description: str
    brand: str | None = None
    category: str | None = None
    unit_price: float
    stock_available: int = 0
    image_url: str | None = None


class SupplierProductUpdate(BaseModel):
    description: str | None = None
    unit_price: float | None = None
    stock_available: int | None = None
    is_active: bool | None = None
    brand: str | None = None
    category: str | None = None
    image_url: str | None = None


class SupplierInfo(BaseModel):
    id: int
    name: str
    region: str | None = None
    product_count: int

    class Config:
        from_attributes = True


class MarketplaceSearchResult(BaseModel):
    count: int
    results: list[SupplierProductOut]


# --- Authenticated supplier endpoints ---

@router.get("/products", response_model=list[SupplierProductOut])
def list_my_products(
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """List products from the authenticated supplier's catalog."""
    return (
        db.query(SupplierProduct)
        .filter(SupplierProduct.tenant_id == tenant.id, SupplierProduct.is_active == True)
        .order_by(SupplierProduct.description)
        .all()
    )


@router.post("/products", response_model=SupplierProductOut, status_code=201)
def create_product(
    data: SupplierProductCreate,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Add a product to the supplier's catalog."""
    if tenant.type != TenantType.SUPPLIER:
        raise HTTPException(status_code=403, detail="Only suppliers can list products")

    product = SupplierProduct(tenant_id=tenant.id, **data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


@router.patch("/products/{product_id}", response_model=SupplierProductOut)
def update_product(
    product_id: int,
    data: SupplierProductUpdate,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Update a product in the supplier's catalog."""
    product = (
        db.query(SupplierProduct)
        .filter(SupplierProduct.id == product_id, SupplierProduct.tenant_id == tenant.id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(product, field, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/products/{product_id}", status_code=204)
def deactivate_product(
    product_id: int,
    tenant: Tenant = Depends(require_tenant_token),
    db: Session = Depends(get_db),
):
    """Deactivate (soft-delete) a product."""
    product = (
        db.query(SupplierProduct)
        .filter(SupplierProduct.id == product_id, SupplierProduct.tenant_id == tenant.id)
        .first()
    )
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    product.is_active = False
    db.commit()


# --- Public marketplace endpoints ---

@router.get("/search", response_model=MarketplaceSearchResult)
def search_marketplace(
    q: str = Query(..., min_length=2, max_length=100),
    region: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Search across all active supplier products. Optional region filter."""
    term = f"%{q}%"
    query = (
        db.query(SupplierProduct)
        .join(Tenant, SupplierProduct.tenant_id == Tenant.id)
        .filter(
            SupplierProduct.is_active == True,
            Tenant.is_active == True,
            or_(
                SupplierProduct.description.ilike(term),
                SupplierProduct.brand.ilike(term),
                SupplierProduct.ean.ilike(term),
            ),
        )
    )
    if region:
        query = query.filter(Tenant.region == region)

    products = query.order_by(SupplierProduct.unit_price).limit(limit).all()
    return MarketplaceSearchResult(count=len(products), results=products)


@router.get("/{tenant_id}/products", response_model=list[SupplierProductOut])
def list_supplier_products(
    tenant_id: int,
    db: Session = Depends(get_db),
):
    """List all active products from a specific supplier."""
    return (
        db.query(SupplierProduct)
        .filter(SupplierProduct.tenant_id == tenant_id, SupplierProduct.is_active == True)
        .order_by(SupplierProduct.description)
        .all()
    )
