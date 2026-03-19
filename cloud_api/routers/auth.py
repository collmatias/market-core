"""
Auth router — password reset requests and pending actions management.
"""
import json
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from core.deps import get_db, require_admin
from models.pending_action import PendingAction
from models.license import License

router = APIRouter(prefix="/auth", tags=["Auth"])


# --- Schemas ---

class PasswordResetRequest(BaseModel):
    hw_id: str
    email: str


class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str


class PendingActionCreate(BaseModel):
    hardware_id: str
    action_type: str
    payload: dict | None = None


class PendingActionOut(BaseModel):
    id: int
    hardware_id: str
    action_type: str
    token: str
    is_consumed: bool

    class Config:
        from_attributes = True


# --- Public endpoints ---

@router.post("/password-reset-request", summary="Request password reset")
def password_reset_request(req: PasswordResetRequest, db: Session = Depends(get_db)):
    """Create a pending password reset action for a desktop node."""
    # Verify the license exists
    license_entry = db.query(License).filter(License.hardware_id == req.hw_id).first()
    if not license_entry:
        raise HTTPException(status_code=404, detail="Hardware ID not found")

    # Verify email matches
    if license_entry.company_email != req.email and license_entry.client_email != req.email:
        raise HTTPException(status_code=403, detail="Email does not match this license")

    action = PendingAction(
        hardware_id=req.hw_id,
        action_type="PASSWORD_RESET",
        payload=json.dumps({"email": req.email}),
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db.add(action)
    db.commit()
    db.refresh(action)

    # In the future, send email with the token. For now just return success.
    return {"message": "Password reset action created", "token": action.token}


@router.post("/password-reset-confirm", summary="Confirm password reset")
def password_reset_confirm(req: PasswordResetConfirm, db: Session = Depends(get_db)):
    """Validate token and mark action as consumed. Desktop handles the actual password change."""
    action = db.query(PendingAction).filter(
        PendingAction.token == req.token,
        PendingAction.is_consumed == False
    ).first()

    if not action:
        raise HTTPException(status_code=404, detail="Invalid or already consumed token")

    if action.expires_at and action.expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=410, detail="Token expired")

    action.is_consumed = True
    db.commit()

    return {"message": "Password reset confirmed", "hardware_id": action.hardware_id}


# --- Admin endpoints (JWT required) ---

@router.post("/pending-action", response_model=PendingActionOut, summary="Create pending action (admin)")
def create_pending_action(
    req: PendingActionCreate,
    db: Session = Depends(get_db),
    _: dict = Depends(require_admin),
):
    """Admin-initiated pending action (e.g., force password reset on a node)."""
    action = PendingAction(
        hardware_id=req.hardware_id,
        action_type=req.action_type,
        payload=json.dumps(req.payload) if req.payload else None,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(action)
    db.commit()
    db.refresh(action)
    return action


@router.get("/pending-actions/{hw_id}", response_model=list[PendingActionOut], summary="List pending actions for hw_id")
def list_pending_actions(hw_id: str, db: Session = Depends(get_db), _: dict = Depends(require_admin)):
    return db.query(PendingAction).filter(
        PendingAction.hardware_id == hw_id,
        PendingAction.is_consumed == False
    ).all()
