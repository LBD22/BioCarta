import json
from sqlalchemy.orm import Session
from ..core.db import SessionLocal, Base, engine
from ..models.biomarker import Biomarker
from ..models.synonym import BiomarkerSynonym
from ..models.reference import ReferenceRange
from ..models.unitconv import UnitConversion

def load():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    with open("app/backend/seeds/biomarkers.json", "r", encoding="utf-8") as f:
        items = json.load(f)
        for it in items:
            if not db.query(Biomarker).filter_by(code=it["code"]).first():
                db.add(Biomarker(**it))
    db.commit()
    with open("app/backend/seeds/synonyms.json", "r", encoding="utf-8") as f:
        items = json.load(f)
        for it in items:
            b = db.query(Biomarker).filter_by(code=it["code"]).first()
            if not b: continue
            for s in it["ru"]:
                if not db.query(BiomarkerSynonym).filter_by(biomarker_id=b.id, language="ru", text=s).first():
                    db.add(BiomarkerSynonym(biomarker_id=b.id, language="ru", text=s))
            for s in it["en"]:
                if not db.query(BiomarkerSynonym).filter_by(biomarker_id=b.id, language="en", text=s).first():
                    db.add(BiomarkerSynonym(biomarker_id=b.id, language="en", text=s))
    db.commit()
    # Unit conversions (minimal examples)
    if not db.query(UnitConversion).filter_by(from_unit="mg/dL", to_unit="mmol/L").first():
        db.add(UnitConversion(from_unit="mg/dL", to_unit="mmol/L", factor=0.0555, offset=0))
    if not db.query(UnitConversion).filter_by(from_unit="mmol/L", to_unit="mg/dL").first():
        db.add(UnitConversion(from_unit="mmol/L", to_unit="mg/dL", factor=18.0182, offset=0))
    db.commit()
    # References
    with open("app/backend/seeds/references.json", "r", encoding="utf-8") as f:
        items = json.load(f)
        for it in items:
            b = db.query(Biomarker).filter_by(code=it["code"]).first()
            if not b: continue
            exists = db.query(ReferenceRange).filter_by(biomarker_id=b.id, sex=it["sex"], age_min=it["age_min"], age_max=it["age_max"]).first()
            if not exists:
                db.add(ReferenceRange(biomarker_id=b.id, sex=it["sex"], age_min=it["age_min"], age_max=it["age_max"], low=it["low"], high=it["high"], source=it["source"]))
    db.commit()
    db.close()

if __name__ == "__main__":
    load()
