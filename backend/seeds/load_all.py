import json
import logging
from sqlalchemy.orm import Session
from ..core.db import SessionLocal, Base, engine
from ..models.biomarker import Biomarker
from ..models.synonym import BiomarkerSynonym
from ..models.reference import ReferenceRange
from ..models.unitconv import UnitConversion

logger = logging.getLogger(__name__)

def load():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    import os
    base_dir = os.path.dirname(os.path.abspath(__file__))
    logger.info(f"Loading seed data from: {base_dir}")
    
    # Load biomarkers
    biomarkers_file = os.path.join(base_dir, "biomarkers.json")
    logger.info(f"Loading biomarkers from: {biomarkers_file}")
    with open(biomarkers_file, "r", encoding="utf-8") as f:
        items = json.load(f)
        added = 0
        for it in items:
            if not db.query(Biomarker).filter_by(code=it["code"]).first():
                db.add(Biomarker(**it))
                added += 1
        logger.info(f"Added {added} new biomarkers (total in file: {len(items)})")
    db.commit()
    
    # Load synonyms
    synonyms_file = os.path.join(base_dir, "synonyms.json")
    logger.info(f"Loading synonyms from: {synonyms_file}")
    with open(synonyms_file, "r", encoding="utf-8") as f:
        items = json.load(f)
        added = 0
        for it in items:
            b = db.query(Biomarker).filter_by(code=it["code"]).first()
            if not b: continue
            for s in it["ru"]:
                if not db.query(BiomarkerSynonym).filter_by(biomarker_id=b.id, language="ru", text=s).first():
                    db.add(BiomarkerSynonym(biomarker_id=b.id, language="ru", text=s))
                    added += 1
            for s in it["en"]:
                if not db.query(BiomarkerSynonym).filter_by(biomarker_id=b.id, language="en", text=s).first():
                    db.add(BiomarkerSynonym(biomarker_id=b.id, language="en", text=s))
                    added += 1
        logger.info(f"Added {added} new synonyms")
    db.commit()
    
    # Unit conversions (minimal examples)
    logger.info("Loading unit conversions...")
    if not db.query(UnitConversion).filter_by(from_unit="mg/dL", to_unit="mmol/L").first():
        db.add(UnitConversion(from_unit="mg/dL", to_unit="mmol/L", factor=0.0555, offset=0))
    if not db.query(UnitConversion).filter_by(from_unit="mmol/L", to_unit="mg/dL").first():
        db.add(UnitConversion(from_unit="mmol/L", to_unit="mg/dL", factor=18.0182, offset=0))
    db.commit()
    
    # References
    references_file = os.path.join(base_dir, "references.json")
    logger.info(f"Loading references from: {references_file}")
    with open(references_file, "r", encoding="utf-8") as f:
        items = json.load(f)
        added = 0
        for it in items:
            b = db.query(Biomarker).filter_by(code=it["code"]).first()
            if not b: continue
            exists = db.query(ReferenceRange).filter_by(biomarker_id=b.id, sex=it["sex"], age_min=it["age_min"], age_max=it["age_max"]).first()
            if not exists:
                db.add(ReferenceRange(biomarker_id=b.id, sex=it["sex"], age_min=it["age_min"], age_max=it["age_max"], low=it["low"], high=it["high"], source=it["source"]))
                added += 1
        logger.info(f"Added {added} new reference ranges (total in file: {len(items)})")
    db.commit()
    logger.info("Seed data loading completed successfully")
    db.close()

if __name__ == "__main__":
    load()
