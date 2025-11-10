"""
API endpoints for third-party integrations (WHOOP, Oura)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..core.security import get_db, get_current_user
from ..models.user import User
from ..domain.whoop_integration import (
    get_whoop_auth_url,
    exchange_code_for_token as whoop_exchange_token,
    sync_whoop_data
)
from ..domain.oura_integration import (
    get_oura_auth_url,
    exchange_code_for_token as oura_exchange_token,
    sync_oura_data
)

router = APIRouter(prefix="/integrations", tags=["integrations"])


# ==================== WHOOP Integration ====================

@router.get("/whoop/auth")
def whoop_auth(user=Depends(get_current_user)):
    """
    Get WHOOP OAuth authorization URL
    Redirect user to this URL to authorize BioCarta
    """
    state = f"user_{user.id}"
    auth_url = get_whoop_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/whoop/callback")
def whoop_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    WHOOP OAuth callback endpoint
    Exchanges authorization code for access token and stores it
    """
    try:
        # Exchange code for token
        token_data = whoop_exchange_token(code)
        
        # Extract user ID from state
        if state and state.startswith("user_"):
            user_id = int(state.replace("user_", ""))
            user = db.query(User).get(user_id)
            
            if user:
                # Store tokens in user metadata
                if not user.integration_data:
                    user.integration_data = {}
                
                user.integration_data['whoop_access_token'] = token_data['access_token']
                user.integration_data['whoop_refresh_token'] = token_data.get('refresh_token')
                user.integration_data['whoop_token_expires_at'] = token_data.get('expires_in')
                
                db.commit()
                
                return {
                    "message": "WHOOP connected successfully",
                    "redirect": "/dashboard?integration=whoop&status=success"
                }
        
        raise HTTPException(400, "Invalid state parameter")
    
    except Exception as e:
        raise HTTPException(400, f"WHOOP OAuth failed: {str(e)}")


@router.post("/whoop/sync")
def whoop_sync(
    days_back: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Sync WHOOP data to BioCarta
    Imports last N days of data (default: 30, max: 90)
    """
    if not user.integration_data or 'whoop_access_token' not in user.integration_data:
        raise HTTPException(400, "WHOOP not connected. Please authorize first.")
    
    access_token = user.integration_data['whoop_access_token']
    
    try:
        count = sync_whoop_data(db, user, access_token, days_back)
        return {
            "message": f"Successfully imported {count} measurements from WHOOP",
            "count": count
        }
    except Exception as e:
        raise HTTPException(500, f"WHOOP sync failed: {str(e)}")


@router.delete("/whoop/disconnect")
def whoop_disconnect(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Disconnect WHOOP integration
    Removes stored access tokens
    """
    if user.integration_data:
        user.integration_data.pop('whoop_access_token', None)
        user.integration_data.pop('whoop_refresh_token', None)
        user.integration_data.pop('whoop_token_expires_at', None)
        db.commit()
    
    return {"message": "WHOOP disconnected"}


# ==================== Oura Integration ====================

@router.get("/oura/auth")
def oura_auth(user=Depends(get_current_user)):
    """
    Get Oura OAuth authorization URL
    Redirect user to this URL to authorize BioCarta
    """
    state = f"user_{user.id}"
    auth_url = get_oura_auth_url(state)
    return {"auth_url": auth_url}


@router.get("/oura/callback")
def oura_callback(
    code: str = Query(...),
    state: str = Query(None),
    db: Session = Depends(get_db)
):
    """
    Oura OAuth callback endpoint
    Exchanges authorization code for access token and stores it
    """
    try:
        # Exchange code for token
        token_data = oura_exchange_token(code)
        
        # Extract user ID from state
        if state and state.startswith("user_"):
            user_id = int(state.replace("user_", ""))
            user = db.query(User).get(user_id)
            
            if user:
                # Store tokens in user metadata
                if not user.integration_data:
                    user.integration_data = {}
                
                user.integration_data['oura_access_token'] = token_data['access_token']
                user.integration_data['oura_refresh_token'] = token_data.get('refresh_token')
                user.integration_data['oura_token_expires_at'] = token_data.get('expires_in')
                
                db.commit()
                
                return {
                    "message": "Oura connected successfully",
                    "redirect": "/dashboard?integration=oura&status=success"
                }
        
        raise HTTPException(400, "Invalid state parameter")
    
    except Exception as e:
        raise HTTPException(400, f"Oura OAuth failed: {str(e)}")


@router.post("/oura/sync")
def oura_sync(
    days_back: int = Query(30, ge=1, le=90),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Sync Oura data to BioCarta
    Imports last N days of data (default: 30, max: 90)
    """
    if not user.integration_data or 'oura_access_token' not in user.integration_data:
        raise HTTPException(400, "Oura not connected. Please authorize first.")
    
    access_token = user.integration_data['oura_access_token']
    
    try:
        count = sync_oura_data(db, user, access_token, days_back)
        return {
            "message": f"Successfully imported {count} measurements from Oura",
            "count": count
        }
    except Exception as e:
        raise HTTPException(500, f"Oura sync failed: {str(e)}")


@router.delete("/oura/disconnect")
def oura_disconnect(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """
    Disconnect Oura integration
    Removes stored access tokens
    """
    if user.integration_data:
        user.integration_data.pop('oura_access_token', None)
        user.integration_data.pop('oura_refresh_token', None)
        user.integration_data.pop('oura_token_expires_at', None)
        db.commit()
    
    return {"message": "Oura disconnected"}


# ==================== Integration Status ====================

@router.get("/status")
def integration_status(user=Depends(get_current_user)):
    """
    Get status of all integrations
    Returns which integrations are connected
    """
    status = {
        "whoop": {
            "connected": bool(user.integration_data and 'whoop_access_token' in user.integration_data),
            "name": "WHOOP"
        },
        "oura": {
            "connected": bool(user.integration_data and 'oura_access_token' in user.integration_data),
            "name": "Oura Ring"
        }
    }
    
    return status
