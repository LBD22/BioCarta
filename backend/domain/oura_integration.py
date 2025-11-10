"""
Oura Ring API Integration
OAuth 2.0 flow and data sync for Oura Ring wearable device
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from ..models.user import User


# Oura OAuth Configuration
OURA_CLIENT_ID = os.getenv("OURA_CLIENT_ID", "")
OURA_CLIENT_SECRET = os.getenv("OURA_CLIENT_SECRET", "")
OURA_REDIRECT_URI = os.getenv("OURA_REDIRECT_URI", "http://localhost:8080/api/integrations/oura/callback")

OURA_AUTH_URL = "https://cloud.ouraring.com/oauth/authorize"
OURA_TOKEN_URL = "https://api.ouraring.com/oauth/token"
OURA_API_BASE = "https://api.ouraring.com/v2"


# Oura metrics to BioCarta biomarker mapping
OURA_BIOMARKER_MAPPING = {
    'heart_rate': 'HR',
    'hrv': 'HRV',
    'resting_heart_rate': 'RHR',
    'respiratory_rate': 'RESP_RATE',
    'spo2': 'SPO2',
    'body_temperature': 'TEMP',
}


def get_oura_auth_url(state: str = "") -> str:
    """
    Generate Oura OAuth authorization URL
    User will be redirected to this URL to authorize the app
    """
    params = {
        'client_id': OURA_CLIENT_ID,
        'redirect_uri': OURA_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'personal daily heartrate workout tag session spo2',
        'state': state
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{OURA_AUTH_URL}?{query_string}"


def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token
    Returns: {'access_token': '...', 'refresh_token': '...', 'expires_in': 86400}
    """
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': OURA_CLIENT_ID,
        'client_secret': OURA_CLIENT_SECRET,
        'redirect_uri': OURA_REDIRECT_URI
    }
    
    response = requests.post(OURA_TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh expired access token using refresh token
    """
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': OURA_CLIENT_ID,
        'client_secret': OURA_CLIENT_SECRET
    }
    
    response = requests.post(OURA_TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()


def get_oura_personal_info(access_token: str) -> Dict[str, Any]:
    """
    Get user personal information from Oura API
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{OURA_API_BASE}/usercollection/personal_info", headers=headers)
    response.raise_for_status()
    return response.json()


def get_oura_daily_readiness(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get daily readiness data from Oura
    Includes HRV, RHR, body temperature
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    response = requests.get(f"{OURA_API_BASE}/usercollection/daily_readiness", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('data', [])


def get_oura_daily_sleep(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get daily sleep data from Oura
    Includes HRV, RHR, respiratory rate
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    response = requests.get(f"{OURA_API_BASE}/usercollection/daily_sleep", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('data', [])


def get_oura_heart_rate(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get heart rate data from Oura (5-minute intervals)
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    response = requests.get(f"{OURA_API_BASE}/usercollection/heartrate", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('data', [])


def get_oura_spo2(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get SpO2 data from Oura
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start_date': start_date,
        'end_date': end_date
    }
    
    response = requests.get(f"{OURA_API_BASE}/usercollection/daily_spo2", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('data', [])


def sync_oura_data(db: Session, user: User, access_token: str, days_back: int = 30) -> int:
    """
    Sync Oura data to BioCarta database
    Returns number of measurements imported
    """
    count = 0
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Get daily sleep data (HRV, RHR, respiratory rate)
        sleep_data = get_oura_daily_sleep(access_token, start_str, end_str)
        
        for day in sleep_data:
            day_date = day.get('day', '')
            
            # HRV (ms)
            if 'hrv_avg' in day and day['hrv_avg']:
                hrv_biomarker = db.query(Biomarker).filter(Biomarker.code == 'HRV').first()
                if hrv_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=hrv_biomarker.id,
                        value_std=day['hrv_avg'],
                        unit_std='ms',
                        source_type='oura',
                        sample_datetime=day_date
                    )
                    db.add(m)
                    count += 1
            
            # Resting Heart Rate (bpm)
            if 'resting_heart_rate' in day and day['resting_heart_rate']:
                rhr_biomarker = db.query(Biomarker).filter(Biomarker.code == 'RHR').first()
                if rhr_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=rhr_biomarker.id,
                        value_std=day['resting_heart_rate'],
                        unit_std='bpm',
                        source_type='oura',
                        sample_datetime=day_date
                    )
                    db.add(m)
                    count += 1
            
            # Respiratory Rate (breaths/min)
            if 'respiratory_rate' in day and day['respiratory_rate']:
                resp_biomarker = db.query(Biomarker).filter(Biomarker.code == 'RESP_RATE').first()
                if resp_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=resp_biomarker.id,
                        value_std=day['respiratory_rate'],
                        unit_std='breaths/min',
                        source_type='oura',
                        sample_datetime=day_date
                    )
                    db.add(m)
                    count += 1
        
        # Get daily readiness data (body temperature deviation)
        readiness_data = get_oura_daily_readiness(access_token, start_str, end_str)
        
        for day in readiness_data:
            day_date = day.get('day', '')
            
            # Body temperature deviation (°C)
            # Note: Oura provides temperature deviation from baseline, not absolute temperature
            if 'temperature_deviation' in day and day['temperature_deviation']:
                # We could store this as a separate biomarker or skip it
                # For now, skipping as it's not absolute temperature
                pass
        
        # Get SpO2 data
        spo2_data = get_oura_spo2(access_token, start_str, end_str)
        
        for day in spo2_data:
            day_date = day.get('day', '')
            
            # SpO2 average (%)
            if 'spo2_percentage' in day and day['spo2_percentage']:
                spo2_biomarker = db.query(Biomarker).filter(Biomarker.code == 'SPO2').first()
                if spo2_biomarker:
                    # Convert average to percentage
                    avg_spo2 = day['spo2_percentage'].get('average') if isinstance(day['spo2_percentage'], dict) else day['spo2_percentage']
                    
                    if avg_spo2:
                        m = Measurement(
                            user_id=user.id,
                            biomarker_id=spo2_biomarker.id,
                            value_std=avg_spo2,
                            unit_std='%',
                            source_type='oura',
                            sample_datetime=day_date
                        )
                        db.add(m)
                        count += 1
        
        # Get heart rate data (daily average)
        hr_data = get_oura_heart_rate(access_token, start_str, end_str)
        
        # Group by day and calculate average
        daily_hr = {}
        for reading in hr_data:
            timestamp = reading.get('timestamp', '')
            day = timestamp[:10] if timestamp else ''
            bpm = reading.get('bpm')
            
            if day and bpm:
                if day not in daily_hr:
                    daily_hr[day] = []
                daily_hr[day].append(bpm)
        
        # Save daily averages
        hr_biomarker = db.query(Biomarker).filter(Biomarker.code == 'HR').first()
        if hr_biomarker:
            for day, bpms in daily_hr.items():
                avg_hr = sum(bpms) / len(bpms)
                m = Measurement(
                    user_id=user.id,
                    biomarker_id=hr_biomarker.id,
                    value_std=avg_hr,
                    unit_std='bpm',
                    source_type='oura',
                    sample_datetime=day
                )
                db.add(m)
                count += 1
        
        db.commit()
    
    except Exception as e:
        db.rollback()
        raise Exception(f"Oura sync failed: {str(e)}")
    
    return count
