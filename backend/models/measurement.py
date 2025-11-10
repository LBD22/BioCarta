from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.db import Base

class Measurement(Base):
    __tablename__ = "measurements"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"))
    value_std = Column(Float)
    unit_std = Column(String)
    original_name = Column(String)
    original_unit = Column(String)
    original_value = Column(String)
    source_type = Column(String)
    source_id = Column(Integer, nullable=True)
    sample_datetime = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    computed_flag = Column(Boolean, default=False)
    quality_note = Column(String, nullable=True)
    biomarker = relationship("Biomarker")
