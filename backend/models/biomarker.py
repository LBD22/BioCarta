from sqlalchemy import Column, Integer, String, Float, Boolean
from ..core.db import Base

class Biomarker(Base):
    __tablename__ = "biomarkers"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, index=True)
    name_ru = Column(String)
    name_en = Column(String)
    category = Column(String)
    unit_std = Column(String)
    risk_direction = Column(String)
    is_whoop_supported = Column(Boolean, default=False)
    is_genetic = Column(Boolean, default=False)
