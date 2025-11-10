"""
Apple Health Export XML Parser
Parses export.xml from Apple Health and maps to BioCarta biomarkers
"""

import xml.etree.ElementTree as ET
import zipfile
import os
from typing import List, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.parse_candidate import ParseCandidate
from ..models.upload import Upload


# Mapping Apple Health types to BioCarta biomarker codes
APPLE_HEALTH_MAPPING = {
    # Body Measurements
    'HKQuantityTypeIdentifierHeight': 'HEIGHT',
    'HKQuantityTypeIdentifierBodyMass': 'WEIGHT',
    'HKQuantityTypeIdentifierBodyMassIndex': 'BMI',
    'HKQuantityTypeIdentifierBodyFatPercentage': 'BFAT_PCT',
    'HKQuantityTypeIdentifierLeanBodyMass': 'LBM',
    
    # Vital Signs
    'HKQuantityTypeIdentifierHeartRate': 'HR',
    'HKQuantityTypeIdentifierRestingHeartRate': 'RHR',
    'HKQuantityTypeIdentifierBloodPressureSystolic': 'SBP',
    'HKQuantityTypeIdentifierBloodPressureDiastolic': 'DBP',
    'HKQuantityTypeIdentifierRespiratoryRate': 'RESP_RATE',
    'HKQuantityTypeIdentifierBodyTemperature': 'TEMP',
    'HKQuantityTypeIdentifierOxygenSaturation': 'SPO2',
    
    # Activity
    'HKQuantityTypeIdentifierStepCount': 'STEPS',
    'HKQuantityTypeIdentifierDistanceWalkingRunning': 'DISTANCE',
    'HKQuantityTypeIdentifierActiveEnergyBurned': 'CALORIES',
    'HKQuantityTypeIdentifierBasalEnergyBurned': 'BMR_DAILY',
    
    # Sleep (HRV)
    'HKQuantityTypeIdentifierHeartRateVariabilitySDNN': 'HRV',
    
    # Blood Glucose
    'HKQuantityTypeIdentifierBloodGlucose': 'GLU',
}

# Unit conversions
UNIT_CONVERSIONS = {
    'lb': ('kg', 0.453592),  # pounds to kg
    'ft': ('cm', 30.48),  # feet to cm
    'in': ('cm', 2.54),  # inches to cm
    'mi': ('km', 1.60934),  # miles to km
    'Cal': ('kcal', 1.0),  # Calories
    'mg/dL': ('mmol/L', 0.0555),  # Blood glucose mg/dL to mmol/L (for glucose)
}


def parse_apple_health_xml(db: Session, upload: Upload, file_path: str) -> List[ParseCandidate]:
    """
    Parse Apple Health export.xml file
    Extracts health records and maps to BioCarta biomarkers
    """
    candidates = []
    
    try:
        # Handle ZIP file
        if file_path.lower().endswith('.zip'):
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # Extract to temp directory
                extract_dir = file_path.replace('.zip', '_extracted')
                zip_ref.extractall(extract_dir)
                
                # Find export.xml
                xml_path = None
                for root, dirs, files in os.walk(extract_dir):
                    if 'export.xml' in files:
                        xml_path = os.path.join(root, 'export.xml')
                        break
                
                if not xml_path:
                    raise Exception("export.xml not found in ZIP")
                
                file_path = xml_path
        
        # Parse XML
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        # Group records by type and date to avoid duplicates
        records_by_type_date = {}
        
        # Process Record elements
        for record in root.findall('.//Record'):
            record_type = record.get('type', '')
            
            # Skip if not in our mapping
            if record_type not in APPLE_HEALTH_MAPPING:
                continue
            
            biomarker_code = APPLE_HEALTH_MAPPING[record_type]
            value = record.get('value', '')
            unit = record.get('unit', '')
            
            # Get date
            start_date = record.get('startDate', '')
            if start_date:
                try:
                    # Parse ISO format: 2023-01-15 10:30:00 +0000
                    dt = datetime.fromisoformat(start_date.replace(' +0000', ''))
                    date_str = dt.strftime('%d.%m.%Y')
                except:
                    date_str = start_date.split()[0] if ' ' in start_date else start_date
            else:
                date_str = ""
            
            # Convert units if needed
            if unit in UNIT_CONVERSIONS:
                new_unit, factor = UNIT_CONVERSIONS[unit]
                try:
                    value = str(float(value) * factor)
                    unit = new_unit
                except:
                    pass
            
            # Normalize units
            unit = normalize_unit(unit)
            
            # Create key for deduplication (type + date)
            key = f"{biomarker_code}_{date_str}"
            
            # Keep only the latest value for each type+date
            if key not in records_by_type_date:
                records_by_type_date[key] = {
                    'biomarker_code': biomarker_code,
                    'value': value,
                    'unit': unit,
                    'date': date_str,
                    'timestamp': start_date
                }
            else:
                # Compare timestamps and keep the latest
                if start_date > records_by_type_date[key]['timestamp']:
                    records_by_type_date[key] = {
                        'biomarker_code': biomarker_code,
                        'value': value,
                        'unit': unit,
                        'date': date_str,
                        'timestamp': start_date
                    }
        
        # Create ParseCandidates from deduplicated records
        for record_data in records_by_type_date.values():
            pc = ParseCandidate(
                upload_id=upload.id,
                original_name=record_data['biomarker_code'],
                value_raw=record_data['value'],
                unit_raw=record_data['unit'],
                sample_datetime_raw=record_data['date']
            )
            db.add(pc)
            db.commit()
            db.refresh(pc)
            candidates.append(pc)
        
        # Limit to most recent 1000 records to avoid overwhelming the system
        if len(candidates) > 1000:
            candidates = candidates[-1000:]
    
    except Exception as e:
        # Create error candidate
        pc = ParseCandidate(
            upload_id=upload.id,
            original_name="ERROR",
            value_raw=f"Apple Health import error: {str(e)}",
            unit_raw="",
            sample_datetime_raw=""
        )
        db.add(pc)
        db.commit()
        db.refresh(pc)
        return [pc]
    
    return candidates


def normalize_unit(unit: str) -> str:
    """Normalize unit names to standard format"""
    unit_map = {
        'count': '',
        'count/min': 'bpm',
        'mmHg': 'mmHg',
        '%': '%',
        'degC': '°C',
        'degF': '°C',  # Will need conversion
        'cm': 'cm',
        'kg': 'kg',
        'kcal': 'kcal',
        'ms': 'ms',
        'mmol/L': 'mmol/L',
        'mg/dL': 'mmol/L',  # For glucose
    }
    
    return unit_map.get(unit, unit)
