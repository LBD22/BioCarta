from sqlalchemy import Column, Integer, String, DateTime, Date, JSON
from datetime import datetime
from ..core.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    language = Column(String, default="ru")
    sex = Column(String, default="any")
    birthdate = Column(String, nullable=True)
    date_of_birth = Column(Date, nullable=True)  # For BioAge calculations
    integration_data = Column(JSON, nullable=True)  # For storing integration tokens (renamed from metadata to avoid SQLAlchemy conflict)
    created_at = Column(DateTime, default=datetime.utcnow)
