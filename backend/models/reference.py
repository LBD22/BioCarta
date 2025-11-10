from sqlalchemy import Column, Integer, Float, String, ForeignKey
from sqlalchemy.orm import relationship
from ..core.db import Base

class ReferenceRange(Base):
    __tablename__ = "reference_ranges"
    id = Column(Integer, primary_key=True)
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"))
    sex = Column(String, default="any")
    age_min = Column(Integer, default=0)
    age_max = Column(Integer, default=200)
    low = Column(Float)
    high = Column(Float)
    source = Column(String, default="generic")
    biomarker = relationship("Biomarker")
