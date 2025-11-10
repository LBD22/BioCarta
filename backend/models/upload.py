from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from datetime import datetime
from ..core.db import Base

class Upload(Base):
    __tablename__ = "uploads"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    file_path = Column(String)
    file_type = Column(String)
    status = Column(String, default="uploaded")
    lab_name = Column(String, nullable=True)
    sample_date_guess = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
