from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.unitconv import UnitConversion
from ..models.reference import ReferenceRange
from ..models.user import User
from ..models.biomarker import Biomarker
from ..models.synonym import BiomarkerSynonym
from typing import Optional

def convert_unit(db: Session, value: float, from_unit: str, to_unit: str) -> float:
    if from_unit == to_unit:
        return value
    conv = db.query(UnitConversion).filter_by(from_unit=from_unit, to_unit=to_unit).first()
    if not conv:
        return value
    return value * conv.factor + conv.offset

def select_reference(db: Session, biomarker_id: int, user: User) -> Optional[ReferenceRange]:
    q = db.query(ReferenceRange).filter(ReferenceRange.biomarker_id == biomarker_id)
    sex = user.sex if user.sex in ("m", "f") else "any"
    ranges = q.all()
    def score(rr):
        s = 0
        if rr.sex == sex: s += 2
        elif rr.sex == "any": s += 1
        age = None
        if user.birthdate:
            try:
                y = int(user.birthdate.split("-")[0])
                from datetime import datetime
                age = datetime.utcnow().year - y
            except Exception:
                age = None
        if age is not None and rr.age_min <= age <= rr.age_max:
            s += 2
        return s
    if not ranges:
        return None
    return max(ranges, key=score)

def resolve_biomarker(db: Session, original_name: str, auto_create: bool = True) -> Optional[Biomarker]:
    """Resolve biomarker from original name using synonyms, optionally auto-create if not found"""
    # Direct code match
    bm = db.query(Biomarker).filter(Biomarker.code == original_name.upper()).first()
    if bm:
        return bm
    
    # Synonym match (case-insensitive)
    name_lower = original_name.lower().strip()
    syn = db.query(BiomarkerSynonym).filter(
        func.lower(BiomarkerSynonym.text) == name_lower
    ).first()
    if syn:
        return db.query(Biomarker).get(syn.biomarker_id)
    
    # Partial match in biomarker names
    for bm in db.query(Biomarker).all():
        if name_lower in bm.name_en.lower() or name_lower in bm.name_ru.lower():
            return bm
        if bm.name_en.lower() in name_lower or bm.name_ru.lower() in name_lower:
            return bm
    
    # Auto-create new biomarker if not found
    if auto_create:
        return create_biomarker_from_name(db, original_name)
    
    return None


def create_biomarker_from_name(db: Session, name: str) -> Biomarker:
    """Create a new biomarker from an unknown analysis name"""
    # Generate code from name (uppercase, replace spaces with underscores)
    code = name.upper().replace(' ', '_').replace('-', '_')[:20]
    
    # Check if code already exists, add suffix if needed
    existing = db.query(Biomarker).filter(Biomarker.code == code).first()
    if existing:
        suffix = 1
        while db.query(Biomarker).filter(Biomarker.code == f"{code}_{suffix}").first():
            suffix += 1
        code = f"{code}_{suffix}"
    
    # Create new biomarker
    new_biomarker = Biomarker(
        code=code,
        name_en=name,
        name_ru=name,
        category='other',  # Default category
        unit='',  # Will be filled from first measurement
        description='Auto-created from uploaded data'
    )
    
    db.add(new_biomarker)
    db.commit()
    db.refresh(new_biomarker)
    
    # Create synonym for original name
    synonym = BiomarkerSynonym(
        biomarker_id=new_biomarker.id,
        text=name,
        lang='en'
    )
    db.add(synonym)
    db.commit()
    
    return new_biomarker


def status_against_ref(value: float, low: float, high: float):
    if low is None or high is None or high == low:
        return "unknown"
    if value < low or value > high:
        return "out_of_range"
    pos = (value - low) / (high - low)
    if 0.3 <= pos <= 0.7:
        return "optimal"
    return "borderline"
