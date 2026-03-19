"""
Catalog router — public barcode lookup and product search.

Public endpoints (no auth required):
  GET /catalog/lookup/{barcode}  — exact EAN lookup
  GET /catalog/search?q=         — search by name/brand/EAN

Admin endpoints (JWT required):
  POST /catalog/products         — create/update a master product
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import or_
from sqlalchemy.orm import Session

from core.deps import get_db, require_admin
from models.master_product import MasterProduct

router = APIRouter(prefix="/catalog", tags=["Catalog"])


# --- Schemas ---

class ProductOut(BaseModel):
    id: int
    ean: str
    description: str
    brand: str | None = None
    category: str | None = None
    suggested_price: float | None = None
    image_url: str | None = None
    source: str

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    ean: str
    description: str
    brand: str | None = None
    category: str | None = None
    suggested_price: float | None = None
    image_url: str | None = None
    source: str = "manual"


class SearchResult(BaseModel):
    count: int
    results: list[ProductOut]


# --- Public endpoints ---

@router.get("/lookup/{barcode}", response_model=ProductOut | None)
def lookup_barcode(barcode: str, db: Session = Depends(get_db)):
    """Exact barcode/EAN lookup. Returns the product or 404."""
    barcode = barcode.strip()
    product = db.query(MasterProduct).filter(MasterProduct.ean == barcode).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found in catalog")
    return product


@router.get("/search", response_model=SearchResult)
def search_catalog(
    q: str = Query(..., min_length=2, max_length=100),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search products by name, brand, or EAN. Case-insensitive."""
    term = f"%{q}%"
    products = (
        db.query(MasterProduct)
        .filter(
            or_(
                MasterProduct.description.ilike(term),
                MasterProduct.brand.ilike(term),
                MasterProduct.ean.ilike(term),
            )
        )
        .order_by(MasterProduct.description)
        .limit(limit)
        .all()
    )
    return SearchResult(count=len(products), results=products)


# --- Admin endpoints ---

@router.post("/products", response_model=ProductOut)
def create_or_update_product(
    data: ProductCreate,
    admin=Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create a new master product or update if EAN already exists."""
    existing = db.query(MasterProduct).filter(MasterProduct.ean == data.ean).first()
    if existing:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        return existing

    product = MasterProduct(**data.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return product
