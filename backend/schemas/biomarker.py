from pydantic import BaseModel

class BiomarkerOut(BaseModel):
    id: int
    code: str
    name_ru: str
    name_en: str
    category: str
    unit_std: str
    risk_direction: str
    is_whoop_supported: bool
    is_genetic: bool
    class Config:
        from_attributes = True

class ReferenceRangeOut(BaseModel):
    sex: str
    age_min: int
    age_max: int
    low: float
    high: float
    source: str
    class Config:
        from_attributes = True
