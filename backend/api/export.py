from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from datetime import datetime
import io
import csv

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/whoop")
def export_whoop(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Export measurements in WHOOP-compatible CSV format
    Columns: Date, Metric, Value
    """
    measurements = db.query(Measurement).filter(
        Measurement.user_id == user.id
    ).order_by(Measurement.sample_datetime.asc()).all()
    
    if not measurements:
        raise HTTPException(404, "No measurements found")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Date', 'Metric', 'Value'])
    
    for m in measurements:
        bm = db.query(Biomarker).get(m.biomarker_id)
        if not bm:
            continue
        
        # Format date
        try:
            date_obj = datetime.fromisoformat(m.sample_datetime)
            date_str = date_obj.strftime('%Y-%m-%d')
        except:
            date_str = m.sample_datetime[:10]
        
        # Metric name with unit
        metric = f"{bm.name_en} ({bm.unit_std})"
        
        writer.writerow([date_str, metric, m.value_std])
    
    output.seek(0)
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type='text/csv',
        headers={'Content-Disposition': 'attachment; filename=biocarta_whoop_export.csv'}
    )


@router.post("/doctor")
def export_doctor(
    lang: str = "en",
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Export doctor summary in RU/EN
    Returns a formatted text report with latest values and reference ranges
    """
    biomarkers = db.query(Biomarker).all()
    
    # Get latest measurement for each biomarker
    report_lines = []
    
    if lang == "ru":
        report_lines.append("=" * 60)
        report_lines.append("МЕДИЦИНСКАЯ СПРАВКА - РЕЗУЛЬТАТЫ АНАЛИЗОВ")
        report_lines.append("=" * 60)
        report_lines.append(f"Дата формирования: {datetime.utcnow().strftime('%d.%m.%Y')}")
        report_lines.append("")
    else:
        report_lines.append("=" * 60)
        report_lines.append("MEDICAL REPORT - LAB RESULTS")
        report_lines.append("=" * 60)
        report_lines.append(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d')}")
        report_lines.append("")
    
    # Group by category
    categories = {}
    for bm in biomarkers:
        m = db.query(Measurement).filter(
            Measurement.user_id == user.id,
            Measurement.biomarker_id == bm.id
        ).order_by(Measurement.sample_datetime.desc()).first()
        
        if not m:
            continue
        
        if bm.category not in categories:
            categories[bm.category] = []
        
        categories[bm.category].append({
            'biomarker': bm,
            'measurement': m
        })
    
    # Format each category
    for cat, items in sorted(categories.items()):
        cat_name = cat.replace('_', ' ').title()
        if lang == "ru":
            cat_translations = {
                'Blood Test': 'Анализы крови',
                'Anthropometry': 'Антропометрия',
                'Body Composition': 'Состав тела'
            }
            cat_name = cat_translations.get(cat_name, cat_name)
        
        report_lines.append(f"\n{cat_name}")
        report_lines.append("-" * 60)
        
        for item in items:
            bm = item['biomarker']
            m = item['measurement']
            
            name = bm.name_ru if lang == "ru" else bm.name_en
            
            # Format date
            try:
                date_obj = datetime.fromisoformat(m.sample_datetime)
                date_str = date_obj.strftime('%d.%m.%Y' if lang == "ru" else '%Y-%m-%d')
            except:
                date_str = m.sample_datetime[:10]
            
            # Get reference range
            from ..domain.normalize import select_reference
            ref = select_reference(db, bm.id, user)
            
            ref_str = ""
            if ref and ref.low is not None and ref.high is not None:
                ref_str = f" (норма: {ref.low}-{ref.high})" if lang == "ru" else f" (ref: {ref.low}-{ref.high})"
            
            report_lines.append(
                f"  {name}: {m.value_std:.2f} {bm.unit_std}{ref_str} [{date_str}]"
            )
    
    report_lines.append("\n" + "=" * 60)
    if lang == "ru":
        report_lines.append("Конец отчета")
    else:
        report_lines.append("End of Report")
    report_lines.append("=" * 60)
    
    report_text = "\n".join(report_lines)
    
    filename = f"biocarta_doctor_summary_{lang}.txt"
    
    return StreamingResponse(
        io.BytesIO(report_text.encode('utf-8')),
        media_type='text/plain',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )
