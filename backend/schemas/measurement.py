from pydantic import BaseModel

class MeasurementIn(BaseModel):
    biomarker_id: int
    value: float
    unit: str
    sample_datetime: str
    source_type: str = "manual"
    original_name: str | None = None

class MeasurementOut(BaseModel):
    id: int
    biomarker_id: int
    value_std: float
    unit_std: str
    sample_datetime: str
    source_type: str
    original_name: str | None = None
    original_unit: str | None = None
    original_value: str | None = None
    class Config:
        from_attributes = True
