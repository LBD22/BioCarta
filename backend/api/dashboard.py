from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..models.biomarker import Biomarker
from ..models.measurement import Measurement
from ..domain.normalize import select_reference, status_against_ref

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

@router.get("/summary")
def summary(db: Session = Depends(get_db), user=Depends(get_current_user)):
    biomarkers = db.query(Biomarker).all()
    tracked = 0
    optimal = borderline = out = 0
    for bm in biomarkers:
        m = db.query(Measurement).filter(Measurement.user_id == user.id, Measurement.biomarker_id == bm.id)             .order_by(Measurement.sample_datetime.desc()).first()
        if not m:
            continue
        tracked += 1
        rr = select_reference(db, bm.id, user)
        if rr:
            st = status_against_ref(m.value_std, rr.low, rr.high)
            if st == "optimal": optimal += 1
            elif st == "borderline": borderline += 1
            elif st == "out_of_range": out += 1
    return {"tracked": tracked, "optimal": optimal, "borderline": borderline, "out_of_range": out}


@router.get("/overview")
def overview(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Get detailed overview with all tracked biomarkers"""
    biomarkers = db.query(Biomarker).all()
    tracked_biomarkers = []
    
    categories = {}
    
    for bm in biomarkers:
        m = db.query(Measurement).filter(
            Measurement.user_id == user.id,
            Measurement.biomarker_id == bm.id
        ).order_by(Measurement.sample_datetime.desc()).first()
        
        if not m:
            continue
        
        rr = select_reference(db, bm.id, user)
        status = "unknown"
        
        if rr and rr.low is not None and rr.high is not None:
            status = status_against_ref(m.value_std, rr.low, rr.high)
        
        biomarker_data = {
            "id": bm.id,
            "code": bm.code,
            "name": bm.name_en,
            "category": bm.category,
            "value": m.value_std,
            "unit": bm.unit_std,
            "date": m.sample_datetime,
            "status": status,
            "reference": {
                "low": rr.low,
                "high": rr.high
            } if rr else None
        }
        
        tracked_biomarkers.append(biomarker_data)
        
        # Group by category
        if bm.category not in categories:
            categories[bm.category] = []
        categories[bm.category].append(biomarker_data)
    
    # Calculate category stats
    category_stats = {}
    for cat, items in categories.items():
        optimal = sum(1 for i in items if i["status"] == "optimal")
        borderline = sum(1 for i in items if i["status"] == "borderline")
        out = sum(1 for i in items if i["status"] == "out_of_range")
        
        category_stats[cat] = {
            "total": len(items),
            "optimal": optimal,
            "borderline": borderline,
            "out_of_range": out
        }
    
    return {
        "biomarkers": tracked_biomarkers,
        "categories": category_stats,
        "total_tracked": len(tracked_biomarkers)
    }
