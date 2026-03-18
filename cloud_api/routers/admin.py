"""
Admin authentication router — JWT token generation.
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core.auth import create_access_token
from core.config import get_settings

router = APIRouter(prefix="/admin", tags=["Admin"])


class AdminLoginRequest(BaseModel):
    secret: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse, summary="Get admin JWT token")
def admin_login(req: AdminLoginRequest):
    """
    Exchange the API_SECRET for a JWT token.
    Use this token in Authorization: Bearer <token> for admin endpoints.
    """
    settings = get_settings()
    if req.secret != settings.api_secret:
        raise HTTPException(status_code=403, detail="Invalid secret")

    token = create_access_token(subject="admin", extra={"role": "admin"})
    return TokenResponse(access_token=token)
