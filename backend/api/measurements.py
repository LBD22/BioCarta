from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..schemas.measurement import MeasurementIn, MeasurementOut
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from ..domain.normalize import convert_unit, select_reference, status_against_ref

router = APIRouter(prefix="/measurements", tags=["measurements"])

@router.get("", response_model=list[MeasurementOut])
def list_measurements(biomarker_id: int | None = None, db: Session = Depends(get_db), user=Depends(get_current_user)):
    q = db.query(Measurement).filter(Measurement.user_id == user.id)
    if biomarker_id:
        q = q.filter(Measurement.biomarker_id == biomarker_id)
    return q.order_by(Measurement.sample_datetime.asc()).all()

@router.post("", response_model=MeasurementOut)
def add_measurement(payload: MeasurementIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bm = db.query(Biomarker).get(payload.biomarker_id)
    if not bm:
        raise HTTPException(400, "Unknown biomarker")
    value_std = convert_unit(db, payload.value, payload.unit, bm.unit_std)
    m = Measurement(
        user_id=user.id, biomarker_id=bm.id,
        value_std=value_std, unit_std=bm.unit_std,
        original_name=payload.original_name or bm.name_en,
        original_unit=payload.unit, original_value=str(payload.value),
        source_type="manual", sample_datetime=payload.sample_datetime
    )
    db.add(m); db.commit(); db.refresh(m)
    return m

@router.delete("/{mid}")
def delete_measurement(mid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    m = db.query(Measurement).get(mid)
    if not m or m.user_id != user.id:
        raise HTTPException(404, "Not found")
    db.delete(m); db.commit()
    return {"message": "deleted"}


@router.get("/stats/{biomarker_id}")
def get_biomarker_stats(biomarker_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Get statistics and latest value for a biomarker"""
    bm = db.query(Biomarker).get(biomarker_id)
    if not bm:
        raise HTTPException(404, "Biomarker not found")
    
    measurements = db.query(Measurement).filter(
        Measurement.user_id == user.id,
        Measurement.biomarker_id == biomarker_id
    ).order_by(Measurement.sample_datetime.desc()).all()
    
    if not measurements:
        return {
            "biomarker": bm,
            "count": 0,
            "latest_value": None,
            "latest_date": None,
            "status": "no_data",
            "reference": None
        }
    
    latest = measurements[0]
    ref = select_reference(db, biomarker_id, user)
    status = "unknown"
    
    if ref and ref.low is not None and ref.high is not None:
        status = status_against_ref(latest.value_std, ref.low, ref.high)
    
    return {
        "biomarker": bm,
        "count": len(measurements),
        "latest_value": latest.value_std,
        "latest_date": latest.sample_datetime,
        "status": status,
        "reference": {
            "low": ref.low,
            "high": ref.high,
            "unit": bm.unit_std
        } if ref else None,
        "history": [
            {
                "date": m.sample_datetime,
                "value": m.value_std,
                "unit": m.unit_std,
                "source": m.source_type,
                "status": status_against_ref(m.value_std, ref.low, ref.high) if ref and ref.low and ref.high else "unknown"
            } for m in measurements  # All measurements
        ]
    }
