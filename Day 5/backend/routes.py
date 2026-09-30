from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.database import get_db
from backend.models import ChatHistory, CreatedEvent
from backend.schemas import (
    ChatRequest, ChatResponse, WeatherInfo, 
    CalendarEventCreate, CalendarEventUpdate, CalendarEventResponse, AuthStatus
)
from backend.agent import run_agent
from backend.weather import get_weather_data
from backend.calendar_tool import list_events, create_event, delete_event, update_event
from backend.auth import get_auth_url, get_oauth_flow, save_credentials, get_credentials, clear_credentials
from backend.utils import logger, parse_date_string

router = APIRouter(prefix="/api")

# Chat endpoints
@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Core AI Agent chat loop endpoint. Decides tool execution and generates final response.
    """
    try:
        return run_agent(db=db, message=request.message, session_id=request.session_id)
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/history", response_model=List[dict])
def get_chat_history(session_id: str, db: Session = Depends(get_db)):
    """
    Retrieves the raw chat logs list for a specific session ID.
    """
    try:
        history = db.query(ChatHistory)\
            .filter(ChatHistory.session_id == session_id)\
            .order_by(ChatHistory.timestamp.asc())\
            .all()
        return [{"role": h.role, "content": h.content, "timestamp": h.timestamp.isoformat()} for h in history]
    except Exception as e:
        logger.error(f"Error reading history: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve history logs.")

@router.get("/chat/history/sessions", response_model=List[str])
def get_chat_sessions(db: Session = Depends(get_db)):
    """
    Returns unique session_ids from ChatHistory to populate history lists in UI.
    """
    try:
        sessions = db.query(ChatHistory.session_id).distinct().all()
        return [s[0] for s in sessions if s[0]]
    except Exception as e:
        logger.error(f"Error reading distinct sessions: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve session history list.")

@router.post("/chat/clear")
def clear_chat_history(session_id: str = Query(...), db: Session = Depends(get_db)):
    """
    Deletes all ChatHistory entries and logs associated with a session ID.
    """
    try:
        db.query(ChatHistory).filter(ChatHistory.session_id == session_id).delete()
        db.commit()
        return {"success": True, "message": f"Session logs for {session_id} successfully cleared."}
    except Exception as e:
        db.rollback()
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to clear session data: {e}")


# Weather endpoints
@router.get("/weather", response_model=dict)
def get_weather_endpoint(city: str = Query(..., description="Target city search term")):
    """
    Retrieve weather info directly for a city.
    """
    try:
        return get_weather_data(city)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Google Calendar endpoints
@router.get("/calendar/events", response_model=List[dict])
def list_calendar_events_endpoint(
    time_min: Optional[str] = None, 
    time_max: Optional[str] = None, 
    q: Optional[str] = None, 
    db: Session = Depends(get_db)
):
    """
    List events from the user's primary calendar.
    """
    try:
        return list_events(db=db, time_min=time_min, time_max=time_max, query=q)
    except PermissionError as p_err:
        raise HTTPException(status_code=401, detail=str(p_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/calendar/create", response_model=dict)
def create_calendar_event_endpoint(event_data: CalendarEventCreate, db: Session = Depends(get_db)):
    """
    Create a Google Calendar event.
    """
    try:
        return create_event(
            db=db,
            summary=event_data.summary,
            start_time=event_data.start_time,
            end_time=event_data.end_time,
            description=event_data.description,
            location=event_data.location,
            recurrence=event_data.recurrence
        )
    except PermissionError as p_err:
        raise HTTPException(status_code=401, detail=str(p_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/calendar/delete")
def delete_calendar_event_endpoint(event_id: str = Query(...), db: Session = Depends(get_db)):
    """
    Delete a Google Calendar event.
    """
    try:
        success = delete_event(db=db, event_id=event_id)
        return {"success": success, "message": "Event deleted successfully."}
    except PermissionError as p_err:
        raise HTTPException(status_code=401, detail=str(p_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/calendar/update", response_model=dict)
def update_calendar_event_endpoint(event_id: str = Query(...), event_data: CalendarEventUpdate = ..., db: Session = Depends(get_db)):
    """
    Update a Google Calendar event.
    """
    try:
        update_dict = event_data.dict(exclude_unset=True)
        return update_event(db=db, event_id=event_id, update_data=update_dict)
    except PermissionError as p_err:
        raise HTTPException(status_code=401, detail=str(p_err))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Authentication OAuth endpoints
@router.get("/auth/status", response_model=AuthStatus)
def check_auth_status_endpoint(db: Session = Depends(get_db)):
    """
    Checks if active credentials exist in the database and returns Google login URL if not.
    """
    try:
        creds = get_credentials(db)
        if creds:
            return AuthStatus(is_connected=True)
        else:
            return AuthStatus(is_connected=False, auth_url=get_auth_url())
    except Exception as e:
        logger.error(f"Error checking credentials status: {e}")
        # Return offline state, but supply auth url
        try:
            url = get_auth_url()
            return AuthStatus(is_connected=False, auth_url=url)
        except Exception:
            return AuthStatus(is_connected=False, auth_url=None)

@router.get("/auth/callback", response_class=HTMLResponse)
def oauth_callback_endpoint(code: str = None, error: str = None, db: Session = Depends(get_db)):
    """
    OAuth Callback handler. Exchanged code for credentials, saves to DB,
    and returns a success HTML confirmation view.
    """
    if error:
        logger.error(f"Google OAuth redirect error: {error}")
        return HTMLResponse(content=f"<h3>Authentication Failed</h3><p>Google returned error: {error}</p>", status_code=400)
    
    if not code:
        raise HTTPException(status_code=400, detail="Missing authorization code parameter.")

    try:
        flow = get_oauth_flow()
        flow.fetch_token(code=code)
        creds = flow.credentials
        
        credentials_dict = {
            "token": creds.token,
            "refresh_token": creds.refresh_token,
            "token_uri": creds.token_uri,
            "scopes": creds.scopes,
            "expiry": creds.expiry.isoformat() if creds.expiry else None
        }
        
        save_credentials(db, credentials_dict)
        
        return """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Authentication Successful</title>
            <style>
                body {
                    background-color: #0b0f19;
                    color: #f3f4f6;
                    font-family: 'Inter', system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                }
                .card {
                    background: rgba(255, 255, 255, 0.03);
                    backdrop-filter: blur(12px);
                    -webkit-backdrop-filter: blur(12px);
                    border: 1px solid rgba(255, 255, 255, 0.08);
                    border-radius: 16px;
                    padding: 40px;
                    max-width: 480px;
                    text-align: center;
                    box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
                }
                h1 {
                    font-size: 24px;
                    background: linear-gradient(135deg, #a855f7 0%, #06b6d4 100%);
                    -webkit-background-clip: text;
                    background-clip: text;
                    -webkit-text-fill-color: transparent;
                    margin-bottom: 16px;
                }
                p {
                    font-size: 15px;
                    color: #9ca3af;
                    line-height: 1.6;
                    margin-bottom: 24px;
                }
                .btn {
                    background: linear-gradient(135deg, #a855f7 0%, #06b6d4 100%);
                    color: white;
                    border: none;
                    padding: 12px 28px;
                    border-radius: 10px;
                    font-weight: 600;
                    font-size: 14px;
                    cursor: pointer;
                    transition: transform 0.2s, box-shadow 0.2s;
                    box-shadow: 0 4px 14px 0 rgba(168, 85, 247, 0.4);
                }
                .btn:hover {
                    transform: translateY(-2px);
                    box-shadow: 0 6px 20px 0 rgba(168, 85, 247, 0.6);
                }
            </style>
        </head>
        <body>
            <div class="card">
                <h1>Google Calendar Linked!</h1>
                <p>Your Google Calendar account has been successfully authorized and integrated with the AI Smart Personal Assistant.</p>
                <p>You can close this window now and return to your chat interface.</p>
                <button class="btn" onclick="window.close()">Close Window</button>
            </div>
        </body>
        </html>
        """
    except Exception as e:
        logger.error(f"Error handling oauth callback: {e}")
        return HTMLResponse(
            content=f"""
            <div style="background-color:#1e1b4b; color:#fda4af; padding:30px; border-radius:10px; font-family:sans-serif; text-align:center; margin:10% auto; max-width:500px; border: 1px solid #f43f5e;">
                <h2>Connection Failed</h2>
                <p>{str(e)}</p>
                <p>Please return to the dashboard and try again.</p>
            </div>
            """, 
            status_code=500
        )

@router.post("/auth/disconnect")
def oauth_disconnect_endpoint(db: Session = Depends(get_db)):
    """
    Clears the Google Calendar OAuth token records from database (log out).
    """
    try:
        clear_credentials(db)
        return {"success": True, "message": "Google Account unlinked successfully."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
