"""
Tenant router — public registration and admin management.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from core.deps import get_db, require_admin
from models.tenant import Tenant, TenantType

router = APIRouter(prefix="/tenant", tags=["Tenant"])


# --- Schemas ---

class TenantRegisterRequest(BaseModel):
    name: str
    email: EmailStr
    tax_id: str | None = None
    phone: str | None = None
    address: str | None = None
    region: str | None = None
    type: TenantType = TenantType.VET


class TenantOut(BaseModel):
    id: int
    name: str
    email: str
    type: TenantType
    plan: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# --- Public endpoints ---

@router.post("/register", response_model=TenantOut, summary="Register a new tenant (public)")
def register_tenant(req: TenantRegisterRequest, db: Session = Depends(get_db)):
    """Public registration — creates a new tenant with FREE plan."""
    # Check email uniqueness
    existing = db.query(Tenant).filter(Tenant.email == req.email).first()
    if existing:
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check tax_id uniqueness if provided
    if req.tax_id:
        existing_tax = db.query(Tenant).filter(Tenant.tax_id == req.tax_id).first()
        if existing_tax:
            raise HTTPException(status_code=409, detail="Tax ID already registered")

    tenant = Tenant(
        name=req.name,
        email=req.email,
        type=req.type,
        tax_id=req.tax_id,
        phone=req.phone,
        address=req.address,
        region=req.region,
        plan="TRIAL",
        is_active=True,
    )
    db.add(tenant)
    db.commit()
    db.refresh(tenant)
    return tenant


# --- Admin endpoints (JWT required) ---

@router.get("/admin/list", response_model=list[TenantOut], summary="List all tenants")
def list_tenants(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    return db.query(Tenant).order_by(Tenant.created_at.desc()).all()


@router.get("/admin/{tenant_id}", response_model=TenantOut, summary="Get tenant by ID")
def get_tenant(
    tenant_id: int,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")
    return tenant


@router.patch("/admin/{tenant_id}", response_model=TenantOut, summary="Update tenant")
def update_tenant(
    tenant_id: int,
    updates: dict,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    allowed_fields = {"name", "phone", "address", "region", "plan", "is_active"}
    for key, value in updates.items():
        if key in allowed_fields:
            setattr(tenant, key, value)

    db.commit()
    db.refresh(tenant)
    return tenant
