from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..core.security import get_db, get_current_user
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from ..domain.normalize import select_reference, status_against_ref
from datetime import datetime

router = APIRouter(prefix="/timeline", tags=["timeline"])

@router.get("")
def get_timeline(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Get all measurements grouped by date"""
    measurements = db.query(Measurement).filter(
        Measurement.user_id == user.id
    ).order_by(Measurement.sample_datetime.desc()).all()
    
    # Group by date
    by_date = {}
    for m in measurements:
        date_str = m.sample_datetime.split('T')[0] if 'T' in m.sample_datetime else m.sample_datetime.split()[0]
        if date_str not in by_date:
            by_date[date_str] = []
        
        bm = db.query(Biomarker).get(m.biomarker_id)
        ref = select_reference(db, m.biomarker_id, user)
        status = "unknown"
        if ref and ref.low and ref.high:
            status = status_against_ref(m.value_std, ref.low, ref.high)
        
        by_date[date_str].append({
            "id": m.id,
            "biomarker_code": bm.code,
            "biomarker_name": bm.name_ru,
            "value": m.value_std,
            "unit": m.unit_std,
            "status": status,
            "source": m.source_type,
            "reference": {
                "low": ref.low,
                "high": ref.high
            } if ref else None
        })
    
    # Convert to list sorted by date
    timeline = [
        {
            "date": date,
            "count": len(items),
            "measurements": items
        }
        for date, items in sorted(by_date.items(), reverse=True)
    ]
    
    return timeline


@router.get("/stats")
def get_overall_stats(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Get overall statistics"""
    total_measurements = db.query(func.count(Measurement.id)).filter(
        Measurement.user_id == user.id
    ).scalar()
    
    unique_biomarkers = db.query(func.count(func.distinct(Measurement.biomarker_id))).filter(
        Measurement.user_id == user.id
    ).scalar()
    
    # Get date range
    first_measurement = db.query(Measurement).filter(
        Measurement.user_id == user.id
    ).order_by(Measurement.sample_datetime.asc()).first()
    
    last_measurement = db.query(Measurement).filter(
        Measurement.user_id == user.id
    ).order_by(Measurement.sample_datetime.desc()).first()
    
    return {
        "total_measurements": total_measurements,
        "unique_biomarkers": unique_biomarkers,
        "first_date": first_measurement.sample_datetime if first_measurement else None,
        "last_date": last_measurement.sample_datetime if last_measurement else None
    }
