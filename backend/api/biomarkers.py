from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..schemas.biomarker import BiomarkerOut, ReferenceRangeOut
from ..models.biomarker import Biomarker
from ..models.reference import ReferenceRange

router = APIRouter(prefix="/biomarkers", tags=["biomarkers"])

@router.get("", response_model=list[BiomarkerOut])
def list_biomarkers(db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Biomarker).all()

@router.get("/{bm_id}", response_model=BiomarkerOut)
def get_biomarker(bm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    bm = db.query(Biomarker).get(bm_id)
    if not bm:
        raise HTTPException(404, "Not found")
    return bm

@router.get("/{bm_id}/reference-ranges", response_model=list[ReferenceRangeOut])
def get_refs(bm_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    refs = db.query(ReferenceRange).filter(ReferenceRange.biomarker_id == bm_id).all()
    return refs
