"""
License management router — check and admin CRUD.
"""
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import or_

from core.deps import get_db, require_admin
from models.license import License

router = APIRouter(prefix="/license", tags=["License"])


# --- Schemas ---

class LicenseCheckRequest(BaseModel):
    hw_id: str


class LicenseCheckResponse(BaseModel):
    status: str
    expires: str | None = None
    reason: str | None = None
    pending_actions: list[str] = []


class LicenseCreateRequest(BaseModel):
    hw_id: str
    client_name: str
    client_email: str | None = None
    company_name: str | None = None
    company_email: str | None = None
    company_tax_id: str | None = None
    plan: str = "MONTHLY"
    expiration_date: date | None = None


class LicenseUpdateRequest(BaseModel):
    client_name: str | None = None
    client_email: str | None = None
    company_name: str | None = None
    company_email: str | None = None
    company_tax_id: str | None = None
    plan: str | None = None
    expiration_date: date | None = None
    notes: str | None = None
    is_active: bool | None = None


class LicenseTransferRequest(BaseModel):
    old_hw_id: str
    new_hw_id: str


class LicenseOut(BaseModel):
    hardware_id: str
    client_name: str
    client_email: str | None = None
    company_name: str | None = None
    company_email: str | None = None
    company_tax_id: str | None = None
    plan: str | None = None
    expiration_date: date | None = None
    is_active: bool
    notes: str | None = None

    class Config:
        from_attributes = True


# --- Public endpoints ---

@router.post("/check", response_model=LicenseCheckResponse, summary="Check license status")
def check_license(req: LicenseCheckRequest, db: Session = Depends(get_db)):
    """Consumed by Desktop installations to validate their license."""
    entry = db.query(License).filter(License.hardware_id == req.hw_id).first()

    if not entry:
        return LicenseCheckResponse(status="DENIED", reason="Not Found")

    if not entry.is_active:
        return LicenseCheckResponse(status="DENIED", reason="Revoked")

    # Perpetual license: no expiration date
    if entry.expiration_date is None:
        return LicenseCheckResponse(status="ACTIVE", expires=None)

    # Check pending actions for this hardware
    pending = []
    try:
        from models.pending_action import PendingAction
        actions = db.query(PendingAction).filter(
            PendingAction.hardware_id == req.hw_id,
            PendingAction.is_consumed == False
        ).all()
        pending = [a.action_type for a in actions]
    except Exception:
        pass

    if entry.expiration_date >= date.today():
        return LicenseCheckResponse(
            status="ACTIVE",
            expires=entry.expiration_date.isoformat(),
            pending_actions=pending
        )
    else:
        return LicenseCheckResponse(
            status="EXPIRED",
            expires=entry.expiration_date.isoformat(),
            pending_actions=pending
        )


# --- Legacy compatibility (old Desktop clients use /check-license) ---

@router.post("/check-license", include_in_schema=False)
def check_license_legacy(req: LicenseCheckRequest, db: Session = Depends(get_db)):
    """Backward-compatible endpoint for existing installations."""
    return check_license(req, db)


# --- Admin endpoints (JWT required) ---

@router.get("/admin/list", response_model=list[LicenseOut], summary="List all licenses")
def list_licenses(
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
    is_active: Optional[str] = Query(None),
    plan: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
):
    query = db.query(License)

    if is_active is not None:
        query = query.filter(License.is_active == (is_active.lower() == 'true'))
    if plan:
        query = query.filter(License.plan == plan)
    if search:
        pattern = f"%{search}%"
        query = query.filter(or_(
            License.hardware_id.ilike(pattern),
            License.client_name.ilike(pattern),
            License.company_name.ilike(pattern),
            License.client_email.ilike(pattern),
        ))

    return query.order_by(License.created_at.desc()).all()


@router.get("/admin/{hw_id}", response_model=LicenseOut, summary="Get single license")
def get_license(hw_id: str, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    entry = db.query(License).filter(License.hardware_id == hw_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="License not found")
    return entry


@router.post("/admin/create", response_model=LicenseOut, summary="Create or renew a license")
def create_license(
    req: LicenseCreateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    existing = db.query(License).filter(License.hardware_id == req.hw_id).first()

    if existing:
        existing.expiration_date = req.expiration_date
        existing.is_active = True
        existing.client_name = req.client_name
        if req.client_email is not None:
            existing.client_email = req.client_email
        if req.company_name is not None:
            existing.company_name = req.company_name
        if req.company_email is not None:
            existing.company_email = req.company_email
        if req.company_tax_id is not None:
            existing.company_tax_id = req.company_tax_id
        if req.plan:
            existing.plan = req.plan
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_license = License(
            hardware_id=req.hw_id,
            client_name=req.client_name,
            client_email=req.client_email,
            company_name=req.company_name,
            company_email=req.company_email,
            company_tax_id=req.company_tax_id,
            plan=req.plan,
            expiration_date=req.expiration_date,
        )
        db.add(new_license)
        db.commit()
        db.refresh(new_license)
        return new_license


@router.patch("/admin/{hw_id}", response_model=LicenseOut, summary="Update a license")
def update_license(
    hw_id: str,
    req: LicenseUpdateRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    entry = db.query(License).filter(License.hardware_id == hw_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="License not found")

    update_data = req.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(entry, field, value)

    db.commit()
    db.refresh(entry)
    return entry


@router.post("/admin/revoke/{hw_id}", summary="Revoke a license")
def revoke_license(hw_id: str, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    entry = db.query(License).filter(License.hardware_id == hw_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="License not found")
    entry.is_active = False
    db.commit()
    return {"message": "License revoked", "hw_id": hw_id}


@router.post("/transfer", response_model=LicenseOut, summary="Transfer license to new hardware")
def transfer_license(
    req: LicenseTransferRequest,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    old = db.query(License).filter(License.hardware_id == req.old_hw_id).first()
    if not old:
        raise HTTPException(status_code=404, detail="Source license not found")

    # Revoke old
    old.is_active = False
    old.notes = (old.notes or "") + f"\nTransferred to {req.new_hw_id}"

    # Create new with same company data
    new_license = License(
        hardware_id=req.new_hw_id,
        client_name=old.client_name,
        client_email=old.client_email,
        company_name=old.company_name,
        company_email=old.company_email,
        company_tax_id=old.company_tax_id,
        plan=old.plan,
        expiration_date=old.expiration_date,
        notes=f"Transferred from {req.old_hw_id}",
    )
    db.add(new_license)
    db.commit()
    db.refresh(new_license)
    return new_license
