"""
License management router — check and admin CRUD.
"""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

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


class LicenseCreateRequest(BaseModel):
    hw_id: str
    client_name: str
    expiration_date: date


class LicenseOut(BaseModel):
    hardware_id: str
    client_name: str
    expiration_date: date
    is_active: bool

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

    if entry.expiration_date >= date.today():
        return LicenseCheckResponse(status="ACTIVE", expires=entry.expiration_date.isoformat())
    else:
        return LicenseCheckResponse(status="EXPIRED", expires=entry.expiration_date.isoformat())


# --- Legacy compatibility (old Desktop clients use /check-license) ---

@router.post("/check-license", include_in_schema=False)
def check_license_legacy(req: LicenseCheckRequest, db: Session = Depends(get_db)):
    """Backward-compatible endpoint for existing installations."""
    return check_license(req, db)


# --- Admin endpoints (JWT required) ---

@router.get("/admin/list", response_model=list[LicenseOut], summary="List all licenses")
def list_licenses(db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    return db.query(License).order_by(License.created_at.desc()).all()


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
        db.commit()
        db.refresh(existing)
        return existing
    else:
        new_license = License(
            hardware_id=req.hw_id,
            client_name=req.client_name,
            expiration_date=req.expiration_date,
        )
        db.add(new_license)
        db.commit()
        db.refresh(new_license)
        return new_license


@router.post("/admin/revoke/{hw_id}", summary="Revoke a license")
def revoke_license(hw_id: str, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    entry = db.query(License).filter(License.hardware_id == hw_id).first()
    if not entry:
        raise HTTPException(status_code=404, detail="License not found")
    entry.is_active = False
    db.commit()
    return {"message": "License revoked", "hw_id": hw_id}
