"""
WHOOP API Integration
OAuth 2.0 flow and data sync for WHOOP wearable device
"""

import os
import requests
from typing import Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models.measurement import Measurement
from ..models.biomarker import Biomarker
from ..models.user import User


# WHOOP OAuth Configuration
WHOOP_CLIENT_ID = os.getenv("WHOOP_CLIENT_ID", "")
WHOOP_CLIENT_SECRET = os.getenv("WHOOP_CLIENT_SECRET", "")
WHOOP_REDIRECT_URI = os.getenv("WHOOP_REDIRECT_URI", "http://localhost:8080/api/integrations/whoop/callback")

WHOOP_AUTH_URL = "https://api.prod.whoop.com/oauth/oauth2/auth"
WHOOP_TOKEN_URL = "https://api.prod.whoop.com/oauth/oauth2/token"
WHOOP_API_BASE = "https://api.prod.whoop.com/developer/v1"


# WHOOP metrics to BioCarta biomarker mapping
WHOOP_BIOMARKER_MAPPING = {
    'heart_rate': 'HR',
    'resting_heart_rate': 'RHR',
    'hrv': 'HRV',
    'respiratory_rate': 'RESP_RATE',
    'spo2': 'SPO2',
    'skin_temp': 'TEMP',
    'calories': 'CALORIES',
    'weight': 'WEIGHT',
    'body_fat': 'BFAT_PCT',
}


def get_whoop_auth_url(state: str = "") -> str:
    """
    Generate WHOOP OAuth authorization URL
    User will be redirected to this URL to authorize the app
    """
    params = {
        'client_id': WHOOP_CLIENT_ID,
        'redirect_uri': WHOOP_REDIRECT_URI,
        'response_type': 'code',
        'scope': 'read:recovery read:cycles read:sleep read:workout read:profile read:body_measurement',
        'state': state
    }
    
    query_string = '&'.join([f"{k}={v}" for k, v in params.items()])
    return f"{WHOOP_AUTH_URL}?{query_string}"


def exchange_code_for_token(code: str) -> Dict[str, Any]:
    """
    Exchange authorization code for access token
    Returns: {'access_token': '...', 'refresh_token': '...', 'expires_in': 3600}
    """
    data = {
        'grant_type': 'authorization_code',
        'code': code,
        'client_id': WHOOP_CLIENT_ID,
        'client_secret': WHOOP_CLIENT_SECRET,
        'redirect_uri': WHOOP_REDIRECT_URI
    }
    
    response = requests.post(WHOOP_TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()


def refresh_access_token(refresh_token: str) -> Dict[str, Any]:
    """
    Refresh expired access token using refresh token
    """
    data = {
        'grant_type': 'refresh_token',
        'refresh_token': refresh_token,
        'client_id': WHOOP_CLIENT_ID,
        'client_secret': WHOOP_CLIENT_SECRET
    }
    
    response = requests.post(WHOOP_TOKEN_URL, data=data)
    response.raise_for_status()
    return response.json()


def get_whoop_profile(access_token: str) -> Dict[str, Any]:
    """
    Get user profile from WHOOP API
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(f"{WHOOP_API_BASE}/user/profile/basic", headers=headers)
    response.raise_for_status()
    return response.json()


def get_whoop_cycles(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get physiological cycles (daily summaries) from WHOOP
    Date format: YYYY-MM-DD
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start': start_date,
        'end': end_date
    }
    
    response = requests.get(f"{WHOOP_API_BASE}/cycle", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('records', [])


def get_whoop_recovery(access_token: str, start_date: str, end_date: str) -> List[Dict[str, Any]]:
    """
    Get recovery data from WHOOP
    Includes HRV, RHR, respiratory rate, SpO2
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    params = {
        'start': start_date,
        'end': end_date
    }
    
    response = requests.get(f"{WHOOP_API_BASE}/recovery", headers=headers, params=params)
    response.raise_for_status()
    return response.json().get('records', [])


def get_whoop_body_measurements(access_token: str) -> List[Dict[str, Any]]:
    """
    Get body measurements (weight, body fat %) from WHOOP
    """
    headers = {'Authorization': f'Bearer {access_token}'}
    
    response = requests.get(f"{WHOOP_API_BASE}/user/measurement/body", headers=headers)
    response.raise_for_status()
    return response.json().get('records', [])


def sync_whoop_data(db: Session, user: User, access_token: str, days_back: int = 30) -> int:
    """
    Sync WHOOP data to BioCarta database
    Returns number of measurements imported
    """
    count = 0
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days_back)
    start_str = start_date.strftime('%Y-%m-%d')
    end_str = end_date.strftime('%Y-%m-%d')
    
    try:
        # Get recovery data (HRV, RHR, respiratory rate, SpO2)
        recoveries = get_whoop_recovery(access_token, start_str, end_str)
        
        for recovery in recoveries:
            score_data = recovery.get('score', {})
            
            # HRV (ms)
            if 'hrv_rmssd_milli' in score_data:
                hrv_biomarker = db.query(Biomarker).filter(Biomarker.code == 'HRV').first()
                if hrv_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=hrv_biomarker.id,
                        value_std=score_data['hrv_rmssd_milli'],
                        unit_std='ms',
                        source_type='whoop',
                        sample_datetime=recovery.get('created_at', '')[:10]
                    )
                    db.add(m)
                    count += 1
            
            # Resting Heart Rate (bpm)
            if 'resting_heart_rate' in score_data:
                rhr_biomarker = db.query(Biomarker).filter(Biomarker.code == 'RHR').first()
                if rhr_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=rhr_biomarker.id,
                        value_std=score_data['resting_heart_rate'],
                        unit_std='bpm',
                        source_type='whoop',
                        sample_datetime=recovery.get('created_at', '')[:10]
                    )
                    db.add(m)
                    count += 1
            
            # Respiratory Rate (breaths/min)
            if 'respiratory_rate' in score_data:
                resp_biomarker = db.query(Biomarker).filter(Biomarker.code == 'RESP_RATE').first()
                if resp_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=resp_biomarker.id,
                        value_std=score_data['respiratory_rate'],
                        unit_std='breaths/min',
                        source_type='whoop',
                        sample_datetime=recovery.get('created_at', '')[:10]
                    )
                    db.add(m)
                    count += 1
            
            # SpO2 (%)
            if 'spo2_percentage' in score_data:
                spo2_biomarker = db.query(Biomarker).filter(Biomarker.code == 'SPO2').first()
                if spo2_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=spo2_biomarker.id,
                        value_std=score_data['spo2_percentage'],
                        unit_std='%',
                        source_type='whoop',
                        sample_datetime=recovery.get('created_at', '')[:10]
                    )
                    db.add(m)
                    count += 1
        
        # Get body measurements (weight, body fat)
        body_measurements = get_whoop_body_measurements(access_token)
        
        for measurement in body_measurements:
            created_at = measurement.get('created_at', '')[:10]
            
            # Weight (kg)
            if 'weight_kilogram' in measurement:
                weight_biomarker = db.query(Biomarker).filter(Biomarker.code == 'WEIGHT').first()
                if weight_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=weight_biomarker.id,
                        value_std=measurement['weight_kilogram'],
                        unit_std='kg',
                        source_type='whoop',
                        sample_datetime=created_at
                    )
                    db.add(m)
                    count += 1
            
            # Body Fat % (%)
            if 'body_fat_percentage' in measurement:
                bf_biomarker = db.query(Biomarker).filter(Biomarker.code == 'BFAT_PCT').first()
                if bf_biomarker:
                    m = Measurement(
                        user_id=user.id,
                        biomarker_id=bf_biomarker.id,
                        value_std=measurement['body_fat_percentage'],
                        unit_std='%',
                        source_type='whoop',
                        sample_datetime=created_at
                    )
                    db.add(m)
                    count += 1
        
        db.commit()
    
    except Exception as e:
        db.rollback()
        raise Exception(f"WHOOP sync failed: {str(e)}")
    
    return count
