from sqlalchemy import Column, String, Date, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class License(Base):
    __tablename__ = "licenses"

    hardware_id = Column(String, primary_key=True, index=True)
    client_name = Column(String)
    expiration_date = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())