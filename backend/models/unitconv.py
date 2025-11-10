from sqlalchemy import Column, Integer, String, Float
from ..core.db import Base

class UnitConversion(Base):
    __tablename__ = "unit_conversions"
    id = Column(Integer, primary_key=True)
    from_unit = Column(String)
    to_unit = Column(String)
    factor = Column(Float, default=1.0)
    offset = Column(Float, default=0.0)
