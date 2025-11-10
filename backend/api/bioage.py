"""
API endpoints for biological age calculations
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..domain.bioage import (
    calculate_phenoage,
    calculate_simple_bioage,
    calculate_all_bioages
)

router = APIRouter(prefix="/bioage", tags=["bioage"])


@router.get("/phenoage")
def get_phenoage(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Calculate PhenoAge (Levine 2018)
    Requires: Albumin, Creatinine, Glucose, CRP, Lymphocyte %, MCV, RDW, ALP, WBC
    """
    result = calculate_phenoage(db, user)
    
    if 'error' in result:
        raise HTTPException(400, result['error'])
    
    return result


@router.get("/simple")
def get_simple_bioage(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Calculate simplified biological age
    Based on commonly available biomarkers (lipids, glucose, inflammation, liver, kidney, blood)
    """
    result = calculate_simple_bioage(db, user)
    
    if 'error' in result:
        raise HTTPException(400, result['error'])
    
    return result


@router.get("/all")
def get_all_bioages(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Calculate all available biological age metrics
    Returns PhenoAge, Simple BioAge, and average if multiple methods available
    """
    results = calculate_all_bioages(db, user)
    
    if not results:
        raise HTTPException(400, "Insufficient biomarker data to calculate biological age")
    
    return results
