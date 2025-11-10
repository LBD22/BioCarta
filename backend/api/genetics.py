"""
API endpoints for genetics module
Upload and analyze genetic data from 23andMe, AncestryDNA, etc.
"""

import os
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..core.config import settings
from ..models.genetic_variant import GeneticVariant, GeneticReport
from ..domain.genetics_parser import import_genetic_data, get_genetic_summary
from typing import List

router = APIRouter(prefix="/genetics", tags=["genetics"])


@router.post("/upload")
async def upload_genetic_data(
    file: UploadFile = File(...),
    file_type: str = Query('auto', description="23andme, ancestry, promethease, or auto"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Upload genetic data file (23andMe, AncestryDNA, Promethease)
    Supported formats: TXT, JSON
    """
    # Save file
    os.makedirs(settings.storage_dir, exist_ok=True)
    filename = f"{user.id}_genetics_{file.filename}"
    file_path = os.path.join(settings.storage_dir, filename)
    
    with open(file_path, "wb") as f:
        f.write(await file.read())
    
    # Import genetic data
    try:
        report = import_genetic_data(db, user, file_path, file_type)
        
        return {
            "message": f"Successfully imported {report.variant_count} genetic variants",
            "report_id": report.id,
            "variant_count": report.variant_count,
            "status": report.status
        }
    
    except Exception as e:
        raise HTTPException(500, f"Genetic data import failed: {str(e)}")


@router.get("/reports")
def list_genetic_reports(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    List all genetic reports uploaded by user
    """
    reports = db.query(GeneticReport).filter(
        GeneticReport.user_id == user.id
    ).order_by(GeneticReport.created_at.desc()).all()
    
    return reports


@router.get("/variants")
def list_genetic_variants(
    gene: str = Query(None, description="Filter by gene name"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    List genetic variants for user
    Optionally filter by gene
    """
    query = db.query(GeneticVariant).filter(GeneticVariant.user_id == user.id)
    
    if gene:
        query = query.filter(GeneticVariant.gene == gene)
    
    variants = query.all()
    
    return variants


@router.get("/summary")
def genetic_summary(
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get summary of genetic data
    Returns key findings and risk factors
    """
    summary = get_genetic_summary(db, user)
    return summary


@router.get("/variant/{rsid}")
def get_variant_details(
    rsid: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get details for a specific genetic variant (SNP)
    """
    variant = db.query(GeneticVariant).filter(
        GeneticVariant.user_id == user.id,
        GeneticVariant.rsid == rsid
    ).first()
    
    if not variant:
        raise HTTPException(404, f"Variant {rsid} not found")
    
    return variant


@router.delete("/reports/{report_id}")
def delete_genetic_report(
    report_id: int,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Delete genetic report and all associated variants
    """
    report = db.query(GeneticReport).filter(
        GeneticReport.id == report_id,
        GeneticReport.user_id == user.id
    ).first()
    
    if not report:
        raise HTTPException(404, "Report not found")
    
    # Delete associated variants
    db.query(GeneticVariant).filter(
        GeneticVariant.user_id == user.id
    ).delete()
    
    # Delete report
    db.delete(report)
    db.commit()
    
    return {"message": "Genetic report deleted"}
