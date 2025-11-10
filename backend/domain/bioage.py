"""
Biological Age Calculation
Implements multiple biological age algorithms:
- PhenoAge (Levine 2018)
- Klemera-Doubal Method (KDM)
- Simplified BioAge based on key biomarkers
"""

import math
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from ..models.user import User
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker


def get_latest_biomarker_value(db: Session, user: User, biomarker_code: str) -> Optional[float]:
    """Get most recent value for a biomarker"""
    biomarker = db.query(Biomarker).filter(Biomarker.code == biomarker_code).first()
    if not biomarker:
        return None
    
    measurement = db.query(Measurement).filter(
        Measurement.user_id == user.id,
        Measurement.biomarker_id == biomarker.id
    ).order_by(Measurement.created_at.desc()).first()
    
    return measurement.value_std if measurement else None


def calculate_phenoage(db: Session, user: User) -> Dict[str, Any]:
    """
    Calculate PhenoAge (Levine et al. 2018)
    Based on 9 biomarkers + chronological age
    
    Biomarkers:
    - Albumin (g/dL)
    - Creatinine (mg/dL)
    - Glucose (mg/dL)
    - CRP (mg/L)
    - Lymphocyte % (%)
    - Mean Cell Volume (fL)
    - RDW (%)
    - ALP (U/L)
    - WBC (1000 cells/µL)
    """
    
    # Get chronological age
    if not user.date_of_birth:
        return {"error": "Date of birth required"}
    
    from datetime import datetime
    age = (datetime.now() - user.date_of_birth).days / 365.25
    
    # Get biomarker values
    albumin = get_latest_biomarker_value(db, user, 'ALB')  # g/dL
    creatinine = get_latest_biomarker_value(db, user, 'CREAT')  # µmol/L -> need mg/dL
    glucose = get_latest_biomarker_value(db, user, 'GLU')  # mmol/L -> need mg/dL
    crp = get_latest_biomarker_value(db, user, 'CRP')  # mg/L
    lymph_pct = get_latest_biomarker_value(db, user, 'LYMPH_PCT')  # %
    mcv = get_latest_biomarker_value(db, user, 'MCV')  # fL
    rdw = get_latest_biomarker_value(db, user, 'RDW')  # %
    alp = get_latest_biomarker_value(db, user, 'ALP')  # U/L
    wbc = get_latest_biomarker_value(db, user, 'WBC')  # 10^9/L -> need 1000 cells/µL
    
    # Check if we have enough data
    missing = []
    if albumin is None: missing.append('Albumin')
    if creatinine is None: missing.append('Creatinine')
    if glucose is None: missing.append('Glucose')
    if crp is None: missing.append('CRP')
    if lymph_pct is None: missing.append('Lymphocyte %')
    if mcv is None: missing.append('MCV')
    if rdw is None: missing.append('RDW')
    if alp is None: missing.append('ALP')
    if wbc is None: missing.append('WBC')
    
    if missing:
        return {
            "error": "Missing required biomarkers",
            "missing": missing,
            "phenoage": None
        }
    
    # Convert units
    creatinine_mgdl = creatinine * 0.0113  # µmol/L to mg/dL
    glucose_mgdl = glucose * 18.0  # mmol/L to mg/dL
    wbc_thousands = wbc  # 10^9/L is same as 1000 cells/µL
    
    # PhenoAge formula (Levine 2018)
    # xb = sum of weighted biomarkers
    xb = (
        -0.0336 * albumin +
        0.0095 * creatinine_mgdl +
        0.1953 * glucose_mgdl +
        0.0954 * math.log(crp) +
        -0.0120 * lymph_pct +
        0.0268 * mcv +
        0.3306 * rdw +
        0.0019 * alp +
        0.0554 * wbc_thousands +
        -0.0804 * age
    )
    
    # Mortality score
    mortality_score = 1 - math.exp(-1.51714 * math.exp(xb) * math.exp(0.0076927 * age))
    
    # PhenoAge
    phenoage = 141.50225 + math.log(-0.00553 * math.log(1 - mortality_score)) / 0.090165
    
    # Calculate difference from chronological age
    age_delta = phenoage - age
    
    return {
        "phenoage": round(phenoage, 1),
        "chronological_age": round(age, 1),
        "age_delta": round(age_delta, 1),
        "mortality_score": round(mortality_score * 100, 2),
        "interpretation": get_phenoage_interpretation(age_delta)
    }


def calculate_simple_bioage(db: Session, user: User) -> Dict[str, Any]:
    """
    Simplified biological age calculation
    Based on key biomarkers that are commonly available
    
    Uses:
    - Lipid panel (TC, HDL, LDL, TG)
    - Glucose metabolism (GLU, HbA1c)
    - Inflammation (CRP)
    - Liver (ALT, AST)
    - Kidney (Creatinine, eGFR)
    - Blood (Hemoglobin, WBC)
    """
    
    # Get chronological age
    if not user.date_of_birth:
        return {"error": "Date of birth required"}
    
    from datetime import datetime
    age = (datetime.now() - user.date_of_birth).days / 365.25
    
    # Get biomarker values
    biomarkers = {
        'TC': get_latest_biomarker_value(db, user, 'TC'),
        'HDL': get_latest_biomarker_value(db, user, 'HDL'),
        'LDL': get_latest_biomarker_value(db, user, 'LDL'),
        'TG': get_latest_biomarker_value(db, user, 'TG'),
        'GLU': get_latest_biomarker_value(db, user, 'GLU'),
        'HBA1C': get_latest_biomarker_value(db, user, 'HBA1C'),
        'CRP': get_latest_biomarker_value(db, user, 'CRP'),
        'ALT': get_latest_biomarker_value(db, user, 'ALT'),
        'AST': get_latest_biomarker_value(db, user, 'AST'),
        'CREAT': get_latest_biomarker_value(db, user, 'CREAT'),
        'EGFR': get_latest_biomarker_value(db, user, 'EGFR'),
        'HGB': get_latest_biomarker_value(db, user, 'HGB'),
        'WBC': get_latest_biomarker_value(db, user, 'WBC'),
    }
    
    # Calculate aging score (0-100, higher = older)
    score = 0
    count = 0
    
    # Lipids (optimal ranges)
    if biomarkers['TC']:
        # Optimal: <5.2 mmol/L, High: >6.2
        if biomarkers['TC'] < 5.2:
            score += 0
        elif biomarkers['TC'] < 6.2:
            score += 5
        else:
            score += 10
        count += 1
    
    if biomarkers['HDL']:
        # Optimal: >1.5 mmol/L, Low: <1.0
        if biomarkers['HDL'] > 1.5:
            score += 0
        elif biomarkers['HDL'] > 1.0:
            score += 5
        else:
            score += 10
        count += 1
    
    if biomarkers['LDL']:
        # Optimal: <2.6 mmol/L, High: >4.1
        if biomarkers['LDL'] < 2.6:
            score += 0
        elif biomarkers['LDL'] < 4.1:
            score += 5
        else:
            score += 10
        count += 1
    
    if biomarkers['TG']:
        # Optimal: <1.7 mmol/L, High: >2.3
        if biomarkers['TG'] < 1.7:
            score += 0
        elif biomarkers['TG'] < 2.3:
            score += 5
        else:
            score += 10
        count += 1
    
    # Glucose
    if biomarkers['GLU']:
        # Optimal: 4.0-5.6 mmol/L, Prediabetes: 5.6-7.0, Diabetes: >7.0
        if 4.0 <= biomarkers['GLU'] <= 5.6:
            score += 0
        elif biomarkers['GLU'] < 7.0:
            score += 7
        else:
            score += 15
        count += 1
    
    if biomarkers['HBA1C']:
        # Optimal: <5.7%, Prediabetes: 5.7-6.4%, Diabetes: >6.5%
        if biomarkers['HBA1C'] < 5.7:
            score += 0
        elif biomarkers['HBA1C'] < 6.5:
            score += 7
        else:
            score += 15
        count += 1
    
    # Inflammation
    if biomarkers['CRP']:
        # Optimal: <1 mg/L, Moderate: 1-3, High: >3
        if biomarkers['CRP'] < 1:
            score += 0
        elif biomarkers['CRP'] < 3:
            score += 5
        else:
            score += 10
        count += 1
    
    # Liver
    if biomarkers['ALT']:
        # Optimal: <30 U/L, Elevated: >40
        if biomarkers['ALT'] < 30:
            score += 0
        elif biomarkers['ALT'] < 40:
            score += 3
        else:
            score += 8
        count += 1
    
    # Kidney
    if biomarkers['EGFR']:
        # Optimal: >90, Mild decline: 60-89, Moderate: <60
        if biomarkers['EGFR'] > 90:
            score += 0
        elif biomarkers['EGFR'] > 60:
            score += 5
        else:
            score += 12
        count += 1
    
    # Blood
    if biomarkers['HGB']:
        # Optimal: 130-170 g/L (men), 120-150 g/L (women)
        # Simplified: 120-170
        if 120 <= biomarkers['HGB'] <= 170:
            score += 0
        else:
            score += 5
        count += 1
    
    if count == 0:
        return {"error": "No biomarkers available"}
    
    # Average score
    avg_score = score / count
    
    # Convert score to age delta
    # Score 0 = -5 years, Score 10 = +5 years
    age_delta = (avg_score - 5) * 1.0
    
    bioage = age + age_delta
    
    return {
        "bioage": round(bioage, 1),
        "chronological_age": round(age, 1),
        "age_delta": round(age_delta, 1),
        "aging_score": round(avg_score, 1),
        "biomarkers_used": count,
        "interpretation": get_bioage_interpretation(age_delta)
    }


def get_phenoage_interpretation(age_delta: float) -> str:
    """Get interpretation for PhenoAge delta"""
    if age_delta < -5:
        return "Excellent - You are aging significantly slower than average"
    elif age_delta < -2:
        return "Good - You are aging slower than average"
    elif age_delta < 2:
        return "Average - You are aging at a normal rate"
    elif age_delta < 5:
        return "Fair - You are aging faster than average"
    else:
        return "Poor - You are aging significantly faster than average"


def get_bioage_interpretation(age_delta: float) -> str:
    """Get interpretation for simplified BioAge delta"""
    if age_delta < -3:
        return "Excellent biological health - significantly younger than chronological age"
    elif age_delta < -1:
        return "Good biological health - younger than chronological age"
    elif age_delta < 1:
        return "Average biological health - matches chronological age"
    elif age_delta < 3:
        return "Fair biological health - older than chronological age"
    else:
        return "Poor biological health - significantly older than chronological age"


def calculate_all_bioages(db: Session, user: User) -> Dict[str, Any]:
    """
    Calculate all available biological age metrics
    """
    results = {}
    
    # Try PhenoAge
    phenoage = calculate_phenoage(db, user)
    if 'error' not in phenoage:
        results['phenoage'] = phenoage
    
    # Try Simple BioAge
    simple = calculate_simple_bioage(db, user)
    if 'error' not in simple:
        results['simple_bioage'] = simple
    
    # Calculate average if multiple methods available
    if len(results) > 1:
        avg_delta = sum(r['age_delta'] for r in results.values()) / len(results)
        results['average'] = {
            "age_delta": round(avg_delta, 1),
            "interpretation": get_bioage_interpretation(avg_delta)
        }
    
    return results
