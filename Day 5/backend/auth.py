import json
from typing import Optional
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import OAuthCredential
from backend.utils import logger

# Permissions required to manage (create, read, update, delete) Google Calendar events
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_oauth_flow() -> Flow:
    """
    Initializes and returns the Google OAuth2 Flow using settings configurations.
    """
    if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
        raise ValueError("Google Client ID or Client Secret is not set in environment variables.")

    client_config = {
        "web": {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.GOOGLE_REDIRECT_URI]
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.GOOGLE_REDIRECT_URI
    )

def get_auth_url() -> str:
    """
    Generates the Google OAuth consent page URL.
    Specifies 'consent' prompt and 'offline' access type to guarantee we obtain a refresh token.
    """
    flow = get_oauth_flow()
    auth_url, _ = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    return auth_url

def save_credentials(db: Session, credentials_dict: dict):
    """
    Saves or updates OAuth credentials serialized as JSON in the database.
    """
    try:
        db_cred = db.query(OAuthCredential).filter(OAuthCredential.user_id == "default").first()
        if not db_cred:
            db_cred = OAuthCredential(user_id="default", token_data=json.dumps(credentials_dict))
            db.add(db_cred)
        else:
            db_cred.token_data = json.dumps(credentials_dict)
        db.commit()
        logger.info("Google OAuth credentials saved to SQLite database successfully.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to save Google OAuth credentials to database: {e}")
        raise e

def get_credentials(db: Session) -> Optional[Credentials]:
    """
    Retrieves Google OAuth credentials from the database.
    Checks expiration, auto-refreshes if needed using refresh token, and updates DB.
    Returns Google Credentials object or None if not authenticated.
    """
    try:
        db_cred = db.query(OAuthCredential).filter(OAuthCredential.user_id == "default").first()
        if not db_cred:
            logger.warning("No OAuth credentials record found in database.")
            return None

        token_info = json.loads(db_cred.token_data)
        
        credentials = Credentials(
            token=token_info.get("token"),
            refresh_token=token_info.get("refresh_token"),
            token_uri=token_info.get("token_uri", "https://oauth2.googleapis.com/token"),
            client_id=settings.GOOGLE_CLIENT_ID,
            client_secret=settings.GOOGLE_CLIENT_SECRET,
            scopes=token_info.get("scopes", SCOPES)
        )

        # Check if the access token has expired and refresh it using refresh_token
        if credentials.expired or (credentials.valid is False):
            if credentials.refresh_token:
                logger.info("Google OAuth token expired or invalid. Attempting refresh...")
                credentials.refresh(Request())
                
                # Update saved credentials with the new access token
                refreshed_dict = {
                    "token": credentials.token,
                    "refresh_token": credentials.refresh_token,
                    "token_uri": credentials.token_uri,
                    "scopes": credentials.scopes,
                    "expiry": credentials.expiry.isoformat() if credentials.expiry else None
                }
                save_credentials(db, refreshed_dict)
                logger.info("Successfully refreshed Google OAuth token and updated database.")
            else:
                logger.warning("Google OAuth token expired but no refresh token is available.")
                return None

        return credentials
    except Exception as e:
        logger.error(f"Error loading/refreshing Google OAuth credentials: {e}")
        return None

def clear_credentials(db: Session):
    """
    Deletes Google OAuth credentials from database to logout the user.
    """
    try:
        db_cred = db.query(OAuthCredential).filter(OAuthCredential.user_id == "default").first()
        if db_cred:
            db.delete(db_cred)
            db.commit()
            logger.info("Google OAuth credentials removed from database.")
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to clear Google OAuth credentials: {e}")
        raise e
