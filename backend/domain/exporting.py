import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.biomarker import Biomarker
from ..models.measurement import Measurement
from ..core.config import settings
from openpyxl import Workbook
from reportlab.lib.pagesizes import landscape, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors

WHOOP_CODES = set(["TC","LDL","HDL","TG","APOB","LPA","GLU","A1C","CRP","INS","TSH","FT","TESTO","FER","VD","NA","K","CA","MG","CL"])

def export_whoop(db: Session, user_id: int, lang: str = "en", days: int = 365):
    cutoff = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
    rows = []
    for bm in db.query(Biomarker).all():
        if bm.code not in WHOOP_CODES:
            continue
        m = db.query(Measurement).filter(
            Measurement.user_id == user_id,
            Measurement.biomarker_id == bm.id,
            Measurement.sample_datetime >= cutoff
        ).order_by(Measurement.sample_datetime.desc()).first()
        if not m:
            continue
        rows.append([bm.name_en if lang=="en" else bm.name_ru, m.value_std, m.unit_std, m.sample_datetime, bm.code])
    os.makedirs(settings.storage_dir, exist_ok=True)
    xlsx_path = os.path.join(settings.storage_dir, f"whoop_export_{user_id}.xlsx")
    wb = Workbook(); ws = wb.active
    ws.append(["Biomarker","Value","Units","Date","Code"])
    for r in rows: ws.append(r)
    wb.save(xlsx_path)
    pdf_path = os.path.join(settings.storage_dir, f"whoop_export_{user_id}.pdf")
    doc = SimpleDocTemplate(pdf_path, pagesize=landscape(A4), rightMargin=20,leftMargin=20,topMargin=20,bottomMargin=20)
    table = Table([["Biomarker","Value","Units","Date","Code"]] + rows, repeatRows=1)
    table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.lightgrey),('GRID',(0,0),(-1,-1),0.25,colors.grey),('VALIGN',(0,0),(-1,-1),'MIDDLE')]))
    doc.build([table])
    return xlsx_path, pdf_path
