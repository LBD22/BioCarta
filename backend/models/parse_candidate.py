from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from ..core.db import Base

class ParseCandidate(Base):
    __tablename__ = "parse_candidates"
    id = Column(Integer, primary_key=True)
    upload_id = Column(Integer, ForeignKey("uploads.id"))
    original_name = Column(String)
    value_raw = Column(String)
    unit_raw = Column(String)
    sample_datetime_raw = Column(String)
    guessed_biomarker_id = Column(Integer, ForeignKey("biomarkers.id"), nullable=True)
    confidence = Column(Float, default=0.0)
    upload = relationship("Upload", primaryjoin="ParseCandidate.upload_id==Upload.id")
