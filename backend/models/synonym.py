from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from ..core.db import Base

class BiomarkerSynonym(Base):
    __tablename__ = "biomarker_synonyms"
    id = Column(Integer, primary_key=True)
    biomarker_id = Column(Integer, ForeignKey("biomarkers.id"))
    language = Column(String)
    text = Column(String, index=True)
    biomarker = relationship("Biomarker")
