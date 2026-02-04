from fastapi import FastAPI, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import date
from pydantic import BaseModel
from typing import Optional
from mangum import Mangum # <--- ESTO ES LA MAGIA PARA AWS LAMBDA
import os

from database import engine, Base, get_db
from models import License

# Crear tablas automáticamente al iniciar
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VetCore Cloud License Manager")

# --- MANGUM HANDLER ---
# Esta variable 'handler' es lo que configurarás en AWS Lambda como "Entry Point"
handler = Mangum(app)

# --- SCHEMAS (Validación de datos) ---
class LicenseCheckRequest(BaseModel):
    hw_id: str

class LicenseCreateRequest(BaseModel):
    hw_id: str
    client_name: str
    expiration_date: date
    secret: str # Seguridad básica para crear licencias

# --- ENDPOINTS ---

@app.get("/")
def health_check():
    return {"status": "Cloud API Running", "env": "Production-Ready"}

@app.post("/check-license")
def check_license(req: LicenseCheckRequest, db: Session = Depends(get_db)):
    """
    Este endpoint lo consume el software VetCore instalado en la PC del cliente.
    """
    license_entry = db.query(License).filter(License.hardware_id == req.hw_id).first()
    
    # 1. No existe
    if not license_entry:
        return {"status": "DENIED", "reason": "Not Found"}
    
    # 2. Está desactivada manualmente
    if not license_entry.is_active:
        return {"status": "DENIED", "reason": "Revoked"}
    
    # 3. Verificar fecha
    today = date.today()
    if license_entry.expiration_date >= today:
        return {
            "status": "ACTIVE", 
            "expires": license_entry.expiration_date.isoformat()
        }
    else:
        return {
            "status": "EXPIRED", 
            "expires": license_entry.expiration_date.isoformat()
        }

@app.post("/admin/create-license")
def create_license(req: LicenseCreateRequest, db: Session = Depends(get_db)):
    """
    Endpoint administrativo para que TÚ crees licencias (desde Postman o script).
    """
    # Validación de seguridad muy simple (puedes mejorarla)
    if req.secret != os.environ.get("API_SECRET"):
        raise HTTPException(status_code=403, detail="Unauthorized")
        
    # Verificar si ya existe
    existing = db.query(License).filter(License.hardware_id == req.hw_id).first()
    
    if existing:
        # Actualizar (Renovar suscripción)
        existing.expiration_date = req.expiration_date
        existing.is_active = True
        existing.client_name = req.client_name
        db.commit()
        return {"message": "Licencia actualizada/renovada", "hw_id": req.hw_id}
    else:
        # Crear nueva
        new_license = License(
            hardware_id=req.hw_id,
            client_name=req.client_name,
            expiration_date=req.expiration_date
        )
        db.add(new_license)
        db.commit()
        return {"message": "Licencia creada", "hw_id": req.hw_id}