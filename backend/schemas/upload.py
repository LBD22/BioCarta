from pydantic import BaseModel
from datetime import datetime

class UploadOut(BaseModel):
    id: int
    file_path: str
    file_type: str
    status: str
    created_at: datetime
    lab_name: str | None = None
    sample_date_guess: str | None = None
    class Config:
        from_attributes = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }

class ParseCandidateOut(BaseModel):
    id: int
    original_name: str
    value_raw: str
    unit_raw: str
    sample_datetime_raw: str | None = None
    guessed_biomarker_id: int | None = None
    confidence: float
    class Config:
        from_attributes = True

class ApproveIn(BaseModel):
    upload_id: int
    items: list[dict]
