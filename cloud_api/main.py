"""
VetCoreSoft Cloud API — FastAPI application.

Modular architecture with routers for each domain:
  /           — health check
  /license/   — license check and admin CRUD
  /admin/     — JWT token generation
"""
import logging

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from mangum import Mangum

from core.config import get_settings
from core.database import Base, engine

# --- Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("vetcoresoft.cloud")

# --- Rate limiter ---
settings = get_settings()
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.rate_limit_default])

# --- App ---
app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins.split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request logging middleware ---
@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"{request.method} {request.url.path}")
    response: Response = await call_next(request)
    return response


# --- Create tables (dev convenience; production uses Alembic) ---
if settings.debug:
    Base.metadata.create_all(bind=engine)

# --- Register routers ---
from routers.health import router as health_router  # noqa: E402
from routers.license import router as license_router  # noqa: E402
from routers.admin import router as admin_router  # noqa: E402
from routers.auth import router as auth_router  # noqa: E402
from routers.tenant import router as tenant_router  # noqa: E402

app.include_router(health_router)
app.include_router(license_router)
app.include_router(admin_router)
app.include_router(auth_router)
app.include_router(tenant_router)

# --- Legacy backward-compatible endpoint ---
# Old Desktop clients call POST /check-license directly at root level
from routers.license import check_license as _check_license, LicenseCheckRequest  # noqa: E402
from core.database import get_db  # noqa: E402
from fastapi import Depends  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402


@app.post("/check-license", include_in_schema=False)
def legacy_check_license(req: LicenseCheckRequest, db: Session = Depends(get_db)):
    return _check_license(req, db)


# --- Mangum handler for AWS Lambda ---
handler = Mangum(app)
