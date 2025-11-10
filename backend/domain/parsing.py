import pandas as pd
import pdfplumber
import re
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.parse_candidate import ParseCandidate
from ..models.upload import Upload

def parse_tabular(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """Parse CSV/XLSX files with Name/Value/Unit/Date columns"""
    candidates = []
    try:
        if file_path.lower().endswith(".csv"):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception:
        pc = ParseCandidate(upload_id=upload.id, original_name="Unknown", value_raw="", unit_raw="", sample_datetime_raw="")
        db.add(pc); db.commit(); db.refresh(pc)
        return [pc]
    
    cols = {c.strip().lower(): c for c in df.columns}
    name_col = next((cols[k] for k in cols if k in ("name","test","marker","биомаркер","анализ","показатель")), None)
    value_col = next((cols[k] for k in cols if k in ("value","значение","val")), None)
    unit_col = next((cols[k] for k in cols if k in ("unit","единицы","ед","units")), None)
    date_col = next((cols[k] for k in cols if k in ("date","дата","sample_date")), None)
    
    if not name_col or not value_col:
        for _ in range(min(len(df), 30)):
            pc = ParseCandidate(upload_id=upload.id, original_name="Unknown", value_raw="", unit_raw="", sample_datetime_raw="")
            db.add(pc); db.commit(); db.refresh(pc); candidates.append(pc)
        return candidates
    
    for _, row in df.iterrows():
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name=str(row.get(name_col, "")),
            value_raw=str(row.get(value_col, "")),
            unit_raw=str(row.get(unit_col, "")) if unit_col else "",
            sample_datetime_raw=str(row.get(date_col, "")) if date_col else ""
        )
        db.add(pc); db.commit(); db.refresh(pc); candidates.append(pc)
    return candidates


def parse_pdf_lab_report(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """Parse PDF lab reports using pdfplumber and pattern matching"""
    candidates = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Extract date from common patterns (avoid birthdate)
            date_patterns = [
                # Prefer dates with context keywords
                r'(?:Дата\s+(?:анализа|исследования|взятия|забора)|Date\s+(?:of\s+)?(?:analysis|test|sample)).*?(\d{2}[./]\d{2}[./]\d{4})',
                r'(?:Дата|Date)\s*:?\s*(\d{2}[./]\d{2}[./]\d{4})',
                # Avoid dates near "birth" or "рождения"
                r'(?<!рожден)(?<!birth)(?<!DOB)\s+(\d{2}[./]\d{2}[./]\d{4})',
            ]
            sample_date = ""
            all_dates = []
            
            # Collect all dates and filter out birthdates
            for pattern in date_patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    date_str = match.group(1)
                    # Check if this date is near "birth" keywords
                    context_start = max(0, match.start() - 50)
                    context_end = min(len(full_text), match.end() + 50)
                    context = full_text[context_start:context_end].lower()
                    
                    # Skip if near birth-related keywords
                    if any(kw in context for kw in ['рожден', 'birth', 'dob', 'date of birth', 'дата рождения']):
                        continue
                    
                    all_dates.append(date_str)
            
            # Use the most recent date (likely analysis date, not birthdate)
            if all_dates:
                # Parse dates and find most recent
                parsed_dates = []
                for d in all_dates:
                    try:
                        # Try different formats
                        for fmt in ['%d.%m.%Y', '%d/%m/%Y', '%d-%m-%Y']:
                            try:
                                parsed = datetime.strptime(d.replace('/', '.').replace('-', '.'), '%d.%m.%Y')
                                parsed_dates.append((parsed, d))
                                break
                            except:
                                continue
                    except:
                        pass
                
                if parsed_dates:
                    # Sort by date and take the most recent one
                    parsed_dates.sort(key=lambda x: x[0], reverse=True)
                    sample_date = parsed_dates[0][1]
            
            # Common lab test patterns (RU/EN)
            # Format: Test Name | Value | Unit | Reference
            test_patterns = [
                # Pattern: "Glucose 5.2 mmol/L 3.9-6.1"
                r'(Glucose|Глюкоза)\s+(\d+\.?\d*)\s*(mmol/L|ммоль/л)',
                r'(HbA1c|Гликированный гемоглобин)\s+(\d+\.?\d*)\s*(%)',
                r'(Cholesterol|Холестерин общий)\s+(\d+\.?\d*)\s*(mmol/L|ммоль/л)',
                r'(LDL|ЛПНП)\s+(\d+\.?\d*)\s*(mmol/L|ммоль/л)',
                r'(HDL|ЛПВП)\s+(\d+\.?\d*)\s*(mmol/L|ммоль/л)',
                r'(Triglycerides|Триглицериды)\s+(\d+\.?\d*)\s*(mmol/L|ммоль/л)',
                r'(Creatinine|Креатинин)\s+(\d+\.?\d*)\s*(µmol/L|мкмоль/л)',
                r'(ALT|АЛТ)\s+(\d+\.?\d*)\s*(U/L|Ед/л)',
                r'(AST|АСТ)\s+(\d+\.?\d*)\s*(U/L|Ед/л)',
                r'(TSH|ТТГ)\s+(\d+\.?\d*)\s*(mIU/L|мМЕ/л)',
                r'(Vitamin D|Витамин D)\s+(\d+\.?\d*)\s*(ng/mL|нг/мл)',
                r'(Ferritin|Ферритин)\s+(\d+\.?\d*)\s*(ng/mL|нг/мл)',
                r'(Hemoglobin|Гемоглобин)\s+(\d+\.?\d*)\s*(g/L|г/л)',
            ]
            
            for pattern in test_patterns:
                matches = re.finditer(pattern, full_text, re.IGNORECASE)
                for match in matches:
                    name = match.group(1)
                    value = match.group(2)
                    unit = match.group(3) if len(match.groups()) >= 3 else ""
                    
                    pc = ParseCandidate(
                        upload_id=upload.id,
                        original_name=name,
                        value_raw=value,
                        unit_raw=unit,
                        sample_datetime_raw=sample_date
                    )
                    db.add(pc); db.commit(); db.refresh(pc)
                    candidates.append(pc)
            
            # If no patterns matched, try table extraction
            if not candidates:
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        if len(table) < 2:
                            continue
                        
                        # Try to identify columns
                        header = [str(cell).lower() if cell else "" for cell in table[0]]
                        name_idx = next((i for i, h in enumerate(header) if any(k in h for k in ["name", "test", "показатель", "анализ"])), 0)
                        value_idx = next((i for i, h in enumerate(header) if any(k in h for k in ["value", "result", "значение"])), 1 if len(header) > 1 else None)
                        unit_idx = next((i for i, h in enumerate(header) if any(k in h for k in ["unit", "единиц"])), 2 if len(header) > 2 else None)
                        
                        if value_idx is None:
                            continue
                        
                        for row in table[1:]:
                            if len(row) <= max(name_idx, value_idx):
                                continue
                            
                            name = str(row[name_idx]) if row[name_idx] else ""
                            value = str(row[value_idx]) if row[value_idx] else ""
                            unit = str(row[unit_idx]) if unit_idx and len(row) > unit_idx and row[unit_idx] else ""
                            
                            if name and value and value.replace(".", "").replace(",", "").isdigit():
                                pc = ParseCandidate(
                                    upload_id=upload.id,
                                    original_name=name,
                                    value_raw=value.replace(",", "."),
                                    unit_raw=unit,
                                    sample_datetime_raw=sample_date
                                )
                                db.add(pc); db.commit(); db.refresh(pc)
                                candidates.append(pc)
    
    except Exception as e:
        # If parsing fails, create error candidate
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name=f"PDF Parse Error: {str(e)[:100]}",
            value_raw="",
            unit_raw="",
            sample_datetime_raw=""
        )
        db.add(pc); db.commit(); db.refresh(pc)
        candidates.append(pc)
    
    return candidates


def parse_inbody_pdf(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """Parse InBody PDF reports for body composition data"""
    candidates = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Extract date (avoid birthdate)
            all_dates = re.findall(r'(\d{2}[./]\d{2}[./]\d{4})', full_text)
            sample_date = ""
            
            # Filter out birthdates
            for i, date_str in enumerate(all_dates):
                # Get context around this date
                date_pos = full_text.find(date_str)
                context_start = max(0, date_pos - 50)
                context_end = min(len(full_text), date_pos + 50)
                context = full_text[context_start:context_end].lower()
                
                # Skip if near birth keywords
                if any(kw in context for kw in ['birth', 'dob', 'рожден', 'дата рождения']):
                    continue
                
                sample_date = date_str
                break
            
            # InBody specific patterns
            inbody_patterns = {
                'WEIGHT': r'(?:Weight|Вес).*?(\d+\.?\d*)\s*(?:kg|кг)',
                'HEIGHT': r'(?:Height|Рост).*?(\d+\.?\d*)\s*(?:cm|см)',
                'BMI': r'(?:BMI|ИМТ).*?(\d+\.?\d*)',
                'BFAT_PCT': r'(?:Body Fat|Жир).*?(\d+\.?\d*)\s*%',
                'SMM': r'(?:Skeletal Muscle Mass|Скелетная мышечная масса).*?(\d+\.?\d*)\s*(?:kg|кг)',
                'LBM': r'(?:Lean Body Mass|Безжировая масса).*?(\d+\.?\d*)\s*(?:kg|кг)',
                'FFM': r'(?:Fat Free Mass|Жиросвободная).*?(\d+\.?\d*)\s*(?:kg|кг)',
                'TBW_PCT': r'(?:Total Body Water|Общая вода).*?(\d+\.?\d*)\s*%',
                'VFL': r'(?:Visceral Fat|Висцеральный жир).*?(\d+)',
                'BMR': r'(?:Basal Metabolic Rate|Базальный метаболизм|BMR).*?(\d+)\s*(?:kcal|ккал)',
            }
            
            for code, pattern in inbody_patterns.items():
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    value = match.group(1)
                    
                    # Determine unit based on code
                    unit_map = {
                        'WEIGHT': 'kg', 'HEIGHT': 'cm', 'BMI': 'kg/m^2',
                        'BFAT_PCT': '%', 'SMM': 'kg', 'LBM': 'kg', 'FFM': 'kg',
                        'TBW_PCT': '%', 'VFL': 'level', 'BMR': 'kcal/day'
                    }
                    
                    pc = ParseCandidate(
                        upload_id=upload.id,
                        original_name=code,
                        value_raw=value,
                        unit_raw=unit_map.get(code, ""),
                        sample_datetime_raw=sample_date
                    )
                    db.add(pc); db.commit(); db.refresh(pc)
                    candidates.append(pc)
    
    except Exception as e:
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name=f"InBody Parse Error: {str(e)[:100]}",
            value_raw="",
            unit_raw="",
            sample_datetime_raw=""
        )
        db.add(pc); db.commit(); db.refresh(pc)
        candidates.append(pc)
    
    return candidates


def auto_parse_file(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """Auto-detect file type and parse accordingly"""
    file_lower = file_path.lower()
    
    if file_lower.endswith(('.csv', '.xlsx', '.xls')):
        return parse_tabular(db, upload, file_path)
    elif file_lower.endswith('.pdf'):
        # Try InBody first if filename suggests it
        if 'inbody' in file_lower:
            candidates = parse_inbody_pdf(db, upload, file_path)
            if candidates and candidates[0].original_name != "InBody Parse Error":
                return candidates
        
        # Otherwise try general lab report parsing
        return parse_pdf_lab_report(db, upload, file_path)
    else:
        # Unsupported format
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name="Unsupported file format",
            value_raw="",
            unit_raw="",
            sample_datetime_raw=""
        )
        db.add(pc); db.commit(); db.refresh(pc)
        return [pc]


def parse_inbody_pdf(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """
    Parse InBody PDF reports for body composition data
    Extracts: Weight, BMI, Body Fat %, Skeletal Muscle Mass, VFL, BMR, TBW %, etc.
    """
    candidates = []
    
    try:
        with pdfplumber.open(file_path) as pdf:
            full_text = ""
            for page in pdf.pages:
                full_text += page.extract_text() + "\n"
            
            # Extract date
            date_patterns = [
                r'(?:Test\s+Date|Дата\s+измерения|Date)\s*:?\s*(\d{2}[./]\d{2}[./]\d{4})',
                r'(\d{2}[./]\d{2}[./]\d{4})'
            ]
            sample_date = ""
            for pattern in date_patterns:
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    sample_date = match.group(1)
                    break
            
            # InBody-specific patterns (RU/EN)
            inbody_patterns = {
                # Weight
                'WEIGHT': [
                    r'(?:Weight|Вес|Body\s+Weight)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:Вес|Weight).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ],
                # Height
                'HEIGHT': [
                    r'(?:Height|Рост)\s*:?\s*(\d+\.?\d*)\s*(cm|см)',
                    r'(?:Рост|Height).*?(\d+\.?\d*)\s*(?:cm|см)'
                ],
                # BMI
                'BMI': [
                    r'(?:BMI|ИМТ)\s*:?\s*(\d+\.?\d*)',
                    r'(?:Body\s+Mass\s+Index|Индекс\s+массы\s+тела).*?(\d+\.?\d*)'
                ],
                # Body Fat Percentage
                'BFAT_PCT': [
                    r'(?:Body\s+Fat\s+Mass|Жировая\s+масса).*?(\d+\.?\d*)\s*%',
                    r'(?:PBF|Процент\s+жира).*?(\d+\.?\d*)\s*%',
                    r'(?:Body\s+Fat|Жир).*?(\d+\.?\d*)\s*%'
                ],
                # Skeletal Muscle Mass
                'SMM': [
                    r'(?:Skeletal\s+Muscle\s+Mass|Скелетная\s+мышечная\s+масса)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:SMM|СММ).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ],
                # Lean Body Mass
                'LBM': [
                    r'(?:Lean\s+Body\s+Mass|Сухая\s+масса)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:LBM|СМТ).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ],
                # Fat-Free Mass
                'FFM': [
                    r'(?:Fat[\s-]Free\s+Mass|Безжировая\s+масса)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:FFM|БЖМ).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ],
                # Basal Metabolic Rate
                'BMR': [
                    r'(?:Basal\s+Metabolic\s+Rate|Базальный\s+метаболизм)\s*:?\s*(\d+\.?\d*)\s*(kcal|ккал)',
                    r'(?:BMR|БМР).*?(\d+\.?\d*)\s*(?:kcal|ккал)'
                ],
                # Visceral Fat Level
                'VFL': [
                    r'(?:Visceral\s+Fat\s+Level|Уровень\s+висцерального\s+жира)\s*:?\s*(\d+\.?\d*)',
                    r'(?:VFL|УВЖ).*?(\d+\.?\d*)'
                ],
                # Total Body Water Percentage
                'TBW_PCT': [
                    r'(?:Total\s+Body\s+Water|Общая\s+вода).*?(\d+\.?\d*)\s*%',
                    r'(?:TBW|ОВ).*?(\d+\.?\d*)\s*%'
                ],
                # Protein
                'PROTEIN': [
                    r'(?:Protein|Белок)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:Protein|Белок).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ],
                # Mineral
                'MINERAL': [
                    r'(?:Mineral|Минералы)\s*:?\s*(\d+\.?\d*)\s*(kg|кг)',
                    r'(?:Mineral|Минералы).*?(\d+\.?\d*)\s*(?:kg|кг)'
                ]
            }
            
            # Extract each biomarker
            for biomarker_code, patterns in inbody_patterns.items():
                for pattern in patterns:
                    matches = re.finditer(pattern, full_text, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1)
                        unit = match.group(2) if len(match.groups()) >= 2 else ""
                        
                        # Normalize unit
                        if unit.lower() in ['кг', 'kg']:
                            unit = 'kg'
                        elif unit.lower() in ['см', 'cm']:
                            unit = 'cm'
                        elif unit.lower() in ['ккал', 'kcal']:
                            unit = 'kcal'
                        
                        pc = ParseCandidate(
                            upload_id=upload.id,
                            original_name=biomarker_code,
                            value_raw=value,
                            unit_raw=unit,
                            sample_datetime_raw=sample_date
                        )
                        db.add(pc); db.commit(); db.refresh(pc)
                        candidates.append(pc)
                        break  # Only take first match for each biomarker
                    if candidates and candidates[-1].original_name == biomarker_code:
                        break  # Found this biomarker, move to next
            
            # Try table extraction if patterns didn't work well
            if len(candidates) < 3:  # If we found less than 3 markers, try tables
                for page in pdf.pages:
                    tables = page.extract_tables()
                    for table in tables:
                        for row in table:
                            if not row or len(row) < 2:
                                continue
                            
                            # Check if row contains InBody markers
                            row_text = ' '.join([str(cell) for cell in row if cell])
                            
                            for biomarker_code, patterns in inbody_patterns.items():
                                for pattern in patterns:
                                    match = re.search(pattern, row_text, re.IGNORECASE)
                                    if match:
                                        value = match.group(1)
                                        unit = match.group(2) if len(match.groups()) >= 2 else ""
                                        
                                        pc = ParseCandidate(
                                            upload_id=upload.id,
                                            original_name=biomarker_code,
                                            value_raw=value,
                                            unit_raw=unit,
                                            sample_datetime_raw=sample_date
                                        )
                                        db.add(pc); db.commit(); db.refresh(pc)
                                        candidates.append(pc)
                                        break
    
    except Exception as e:
        # Create error candidate
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name="ERROR",
            value_raw=str(e),
            unit_raw="",
            sample_datetime_raw=""
        )
        db.add(pc); db.commit(); db.refresh(pc)
        return [pc]
    
    return candidates if candidates else []


def auto_parse_file(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """Auto-detect file type and parse accordingly"""
    from .apple_health import parse_apple_health_xml
    
    # Check for Apple Health export (ZIP or XML)
    if file_path.lower().endswith('.zip') or file_path.lower().endswith('.xml'):
        # Check if it's Apple Health export
        is_apple_health = False
        if 'apple' in file_path.lower() or 'health' in file_path.lower() or 'export' in file_path.lower():
            is_apple_health = True
        
        if is_apple_health:
            return parse_apple_health_xml(db, upload, file_path)
    
    # Check if it's InBody by looking at filename or content
    is_inbody = False
    if 'inbody' in file_path.lower():
        is_inbody = True
    else:
        # Check PDF content for InBody markers
        if file_path.lower().endswith('.pdf'):
            try:
                with pdfplumber.open(file_path) as pdf:
                    first_page = pdf.pages[0].extract_text() if pdf.pages else ""
                    if 'inbody' in first_page.lower() or 'body composition' in first_page.lower():
                        is_inbody = True
            except:
                pass
    
    # Route to appropriate parser
    if is_inbody:
        return parse_inbody_pdf(db, upload, file_path)
    elif file_path.lower().endswith(('.csv', '.xlsx')):
        return parse_tabular(db, upload, file_path)
    elif file_path.lower().endswith('.pdf'):
        return parse_pdf_lab_report(db, upload, file_path)
    else:
        # Default to lab report for other files
        return parse_pdf_lab_report(db, upload, file_path)
