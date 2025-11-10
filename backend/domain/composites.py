"""
Composite biomarker calculations
According to PRD: Non-HDL, Atherogenic Index, HOMA-IR, eGFR (CKD-EPI 2021)
"""
from sqlalchemy.orm import Session
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from ..models.user import User
from typing import Optional
from datetime import datetime, timedelta
import math


def get_latest_value(db: Session, user_id: int, biomarker_code: str, within_days: int = 30) -> Optional[float]:
    """Get latest measurement value for a biomarker within specified days"""
    bm = db.query(Biomarker).filter(Biomarker.code == biomarker_code).first()
    if not bm:
        return None
    
    cutoff = datetime.utcnow() - timedelta(days=within_days)
    m = db.query(Measurement).filter(
        Measurement.user_id == user_id,
        Measurement.biomarker_id == bm.id,
        Measurement.sample_datetime >= cutoff.isoformat()
    ).order_by(Measurement.sample_datetime.desc()).first()
    
    return m.value_std if m else None


def calculate_non_hdl(db: Session, user: User) -> Optional[float]:
    """Non-HDL Cholesterol = Total Cholesterol - HDL"""
    chol = get_latest_value(db, user.id, "CHOL")
    hdl = get_latest_value(db, user.id, "HDL")
    
    if chol is not None and hdl is not None:
        return chol - hdl
    return None


def calculate_atherogenic_index(db: Session, user: User) -> Optional[float]:
    """Atherogenic Index = Total Cholesterol / HDL"""
    chol = get_latest_value(db, user.id, "CHOL")
    hdl = get_latest_value(db, user.id, "HDL")
    
    if chol is not None and hdl is not None and hdl > 0:
        return chol / hdl
    return None


def calculate_homa_ir(db: Session, user: User) -> Optional[float]:
    """
    HOMA-IR = (Glucose in mmol/L × Insulin in µU/mL) / 22.5
    Note: Requires insulin measurement which may not be available
    """
    glucose = get_latest_value(db, user.id, "GLU")  # mmol/L
    # Insulin not in default biomarkers, would need to be added
    # For now, return None
    return None


def calculate_egfr_ckd_epi_2021(db: Session, user: User) -> Optional[float]:
    """
    eGFR using CKD-EPI 2021 equation (race-free)
    eGFR = 142 × min(Scr/κ, 1)^α × max(Scr/κ, 1)^-1.200 × 0.9938^age × (1.012 if female)
    
    Where:
    - Scr = serum creatinine in mg/dL
    - κ = 0.7 for females, 0.9 for males
    - α = -0.241 for females, -0.302 for males
    """
    creat = get_latest_value(db, user.id, "CREAT")  # µmol/L
    if creat is None:
        return None
    
    # Convert µmol/L to mg/dL
    creat_mg_dl = creat / 88.4
    
    # Get age
    age = None
    if user.birthdate:
        try:
            birth_year = int(user.birthdate.split("-")[0])
            age = datetime.utcnow().year - birth_year
        except:
            pass
    
    if age is None:
        return None
    
    # Determine sex-specific parameters
    if user.sex == "f":
        kappa = 0.7
        alpha = -0.241
        sex_factor = 1.012
    else:  # male or unknown, use male parameters
        kappa = 0.9
        alpha = -0.302
        sex_factor = 1.0
    
    # Calculate eGFR
    min_term = min(creat_mg_dl / kappa, 1.0) ** alpha
    max_term = max(creat_mg_dl / kappa, 1.0) ** -1.200
    age_term = 0.9938 ** age
    
    egfr = 142 * min_term * max_term * age_term * sex_factor
    
    return round(egfr, 1)


def calculate_bmi(db: Session, user: User) -> Optional[float]:
    """BMI = weight (kg) / height (m)^2"""
    weight = get_latest_value(db, user.id, "WEIGHT", within_days=365)  # kg
    height = get_latest_value(db, user.id, "HEIGHT", within_days=365)  # cm
    
    if weight is not None and height is not None and height > 0:
        height_m = height / 100
        bmi = weight / (height_m ** 2)
        return round(bmi, 1)
    return None


def calculate_all_composites(db: Session, user: User) -> dict:
    """Calculate all available composite metrics"""
    return {
        "non_hdl": calculate_non_hdl(db, user),
        "atherogenic_index": calculate_atherogenic_index(db, user),
        "homa_ir": calculate_homa_ir(db, user),
        "egfr": calculate_egfr_ckd_epi_2021(db, user),
        "bmi": calculate_bmi(db, user)
    }


def auto_save_composites(db: Session, user: User):
    """
    Automatically calculate and save composite biomarkers as measurements
    Called after approving new measurements
    """
    composites = calculate_all_composites(db, user)
    
    composite_map = {
        "non_hdl": "NON_HDL",
        "atherogenic_index": "AI",
        "homa_ir": "HOMA_IR",
        "egfr": "EGFR",
        "bmi": "BMI"
    }
    
    for key, code in composite_map.items():
        value = composites.get(key)
        if value is None:
            continue
        
        # Check if biomarker exists
        bm = db.query(Biomarker).filter(Biomarker.code == code).first()
        if not bm:
            continue
        
        # Check if we already have a recent measurement (within 1 day)
        cutoff = datetime.utcnow() - timedelta(days=1)
        existing = db.query(Measurement).filter(
            Measurement.user_id == user.id,
            Measurement.biomarker_id == bm.id,
            Measurement.sample_datetime >= cutoff.isoformat()
        ).first()
        
        if existing:
            # Update existing
            existing.value_std = value
            existing.sample_datetime = datetime.utcnow().isoformat()
        else:
            # Create new
            m = Measurement(
                user_id=user.id,
                biomarker_id=bm.id,
                value_std=value,
                unit_std=bm.unit_std,
                original_name=f"Calculated {code}",
                original_unit=bm.unit_std,
                original_value=str(value),
                source_type="calculated",
                sample_datetime=datetime.utcnow().isoformat()
            )
            db.add(m)
    
    db.commit()
