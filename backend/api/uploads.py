import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..core.config import settings
from ..models.upload import Upload
from ..models.parse_candidate import ParseCandidate
from ..schemas.upload import UploadOut, ParseCandidateOut, ApproveIn
from ..models.biomarker import Biomarker
from ..models.measurement import Measurement
from ..domain.parsing import auto_parse_file
from ..domain.normalize import convert_unit, resolve_biomarker
from ..domain.composites import auto_save_composites

router = APIRouter(prefix="/uploads", tags=["uploads"])

@router.post("", response_model=UploadOut)
async def create_upload(f: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    os.makedirs(settings.storage_dir, exist_ok=True)
    filename = f"{user.id}_{f.filename}"
    path = os.path.join(settings.storage_dir, filename)
    with open(path, "wb") as out:
        out.write(await f.read())
    up = Upload(user_id=user.id, file_path=path, file_type=f.filename.split(".")[-1].lower(), status="uploaded")
    db.add(up); db.commit(); db.refresh(up)
    if up.file_type in ("csv","xlsx","xls","pdf","zip","xml"):
        auto_parse_file(db, up, path)
        up.status = "parsed"; db.commit()
    return up

@router.get("", response_model=list[UploadOut])
def list_uploads(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Upload).filter(Upload.user_id == user.id).order_by(Upload.created_at.desc()).all()

@router.get("/{uid}/candidates", response_model=list[ParseCandidateOut])
def candidates(uid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    up = db.query(Upload).get(uid)
    if not up or up.user_id != user.id:
        raise HTTPException(404, "Not found")
    return db.query(ParseCandidate).filter(ParseCandidate.upload_id == uid).all()

@router.post("/approve")
def approve(payload: ApproveIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    up = db.query(Upload).get(payload.upload_id)
    if not up or up.user_id != user.id:
        raise HTTPException(404, "Not found")
    for it in payload.items:
        pc = db.query(ParseCandidate).get(it["candidate_id"])
        bm = db.query(Biomarker).get(it["biomarker_id"])
        if not pc or not bm: 
            continue
        val = float(it["value"])
        unit = it.get("unit", bm.unit_std)
        val_std = convert_unit(db, val, unit, bm.unit_std)
        m = Measurement(
            user_id=user.id, biomarker_id=bm.id, value_std=val_std, unit_std=bm.unit_std,
            original_name=pc.original_name, original_unit=unit, original_value=str(val),
            source_type="lab_excel" if up.file_type in ("csv","xlsx","xls") else "lab_pdf",
            source_id=up.id, sample_datetime=it.get("sample_datetime","")
        )
        db.add(m)
    db.commit()
    
    # Auto-calculate composite biomarkers
    auto_save_composites(db, user)
    
    return {"message": "approved"}


@router.get("/{uid}/suggestions")
def get_suggestions(uid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Auto-suggest biomarker matches for parse candidates"""
    up = db.query(Upload).get(uid)
    if not up or up.user_id != user.id:
        raise HTTPException(404, "Not found")
    
    candidates = db.query(ParseCandidate).filter(ParseCandidate.upload_id == uid).all()
    suggestions = []
    
    for pc in candidates:
        bm = resolve_biomarker(db, pc.original_name)
        suggestions.append({
            "candidate_id": pc.id,
            "original_name": pc.original_name,
            "value_raw": pc.value_raw,
            "unit_raw": pc.unit_raw,
            "sample_datetime_raw": pc.sample_datetime_raw,
            "suggested_biomarker_id": bm.id if bm else None,
            "suggested_biomarker_code": bm.code if bm else None,
            "suggested_biomarker_name": bm.name_en if bm else None,
            "confidence": "high" if bm else "none"
        })
    
    return suggestions


@router.delete("/{uid}")
def delete_upload(uid: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Delete upload and all related data (candidates, measurements)"""
    up = db.query(Upload).get(uid)
    if not up or up.user_id != user.id:
        raise HTTPException(404, "Not found")
    
    # Delete all measurements created from this upload
    measurements_deleted = db.query(Measurement).filter(
        Measurement.user_id == user.id,
        Measurement.source_id == uid
    ).delete()
    
    # Delete all parse candidates
    candidates_deleted = db.query(ParseCandidate).filter(
        ParseCandidate.upload_id == uid
    ).delete()
    
    # Delete the file from storage
    import os
    if os.path.exists(up.file_path):
        try:
            os.remove(up.file_path)
        except Exception as e:
            print(f"Failed to delete file: {e}")
    
    # Delete the upload record
    db.delete(up)
    db.commit()
    
    return {
        "message": "deleted",
        "upload_id": uid,
        "measurements_deleted": measurements_deleted,
        "candidates_deleted": candidates_deleted
    }
