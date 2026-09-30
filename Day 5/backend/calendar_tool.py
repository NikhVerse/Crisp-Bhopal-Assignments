from datetime import datetime, timezone
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from sqlalchemy.orm import Session
from backend.auth import get_credentials
from backend.models import CreatedEvent
from backend.utils import logger, parse_date_string

def get_calendar_service(db: Session):
    """
    Builds and returns the Google Calendar API service client.
    Raises PermissionError if user is not authenticated.
    """
    creds = get_credentials(db)
    if not creds:
        logger.warning("Attempted to access Google Calendar without active OAuth credentials.")
        raise PermissionError("User is not authenticated with Google Calendar. Please log in first.")
    return build('calendar', 'v3', credentials=creds)

def list_events(db: Session, time_min: Optional[str] = None, time_max: Optional[str] = None, max_results: int = 15, query: Optional[str] = None) -> list:
    """
    Lists Google Calendar events.
    Optionally filters by time range, search term (query), and limits the result size.
    """
    try:
        service = get_calendar_service(db)
        
        # Default time_min to now (in UTC format) if not specified
        if not time_min:
            time_min = datetime.now(timezone.utc).isoformat()
            
        params = {
            "calendarId": "primary",
            "timeMin": time_min,
            "maxResults": max_results,
            "singleEvents": True, # Expands recurring events into individual instances
            "orderBy": "startTime"
        }
        
        if time_max:
            params["timeMax"] = time_max
            
        if query:
            params["q"] = query

        logger.info(f"Listing events: timeMin={time_min}, query={query}")
        events_result = service.events().list(**params).execute()
        events = events_result.get('items', [])
        
        formatted_events = []
        for e in events:
            # Calendar event starts can be dates (all-day) or dateTimes
            start = e.get('start', {})
            end = e.get('end', {})
            start_val = start.get('dateTime') or start.get('date', '')
            end_val = end.get('dateTime') or end.get('date', '')
            
            formatted_events.append({
                "id": e.get('id'),
                "summary": e.get('summary', '(No Title)'),
                "start_time": start_val,
                "end_time": end_val,
                "description": e.get('description', ''),
                "location": e.get('location', ''),
                "html_link": e.get('htmlLink'),
                "status": e.get('status', 'confirmed')
            })
            
        return formatted_events
    except HttpError as e:
        logger.error(f"Google Calendar API list error: {e}")
        raise RuntimeError(f"Google Calendar API failure: {e.reason}")
    except PermissionError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error listing events: {e}")
        raise e

def create_event(db: Session, summary: str, start_time: str, end_time: str, description: Optional[str] = None, location: Optional[str] = None, recurrence: Optional[str] = None) -> dict:
    """
    Creates an event on the user's primary calendar.
    Saves details in the local SQLite table 'created_events'.
    """
    try:
        service = get_calendar_service(db)
        
        event_body = {
            "summary": summary,
            "start": {"dateTime": start_time, "timeZone": "UTC"},
            "end": {"dateTime": end_time, "timeZone": "UTC"},
        }
        
        if description:
            event_body["description"] = description
        if location:
            event_body["location"] = location
        if recurrence:
            # Expecting recurrence as list of RRULE strings e.g. ["RRULE:FREQ=WEEKLY;COUNT=10"]
            event_body["recurrence"] = [recurrence] if isinstance(recurrence, str) else recurrence

        logger.info(f"Creating event: {summary} starting {start_time}")
        created_event = service.events().insert(calendarId="primary", body=event_body).execute()
        
        # Save to local SQLite database
        try:
            start_dt = parse_date_string(start_time)
            end_dt = parse_date_string(end_time)
            
            local_event = CreatedEvent(
                event_id=created_event.get("id"),
                summary=summary,
                start_time=start_dt,
                end_time=end_dt
            )
            db.add(local_event)
            db.commit()
            logger.info("Saved created event reference to local SQLite database.")
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Could not save event reference to local DB (Calendar creation still succeeded): {db_err}")

        return {
            "id": created_event.get("id"),
            "summary": created_event.get("summary"),
            "start_time": start_time,
            "end_time": end_time,
            "html_link": created_event.get("htmlLink"),
            "status": created_event.get("status")
        }
    except HttpError as e:
        logger.error(f"Google Calendar API create error: {e}")
        raise RuntimeError(f"Google Calendar API creation failure: {e.reason}")
    except PermissionError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error creating event: {e}")
        raise e

def delete_event(db: Session, event_id: str) -> bool:
    """
    Deletes an event from the user's primary calendar by ID.
    Removes the reference from local SQLite table if it exists.
    """
    try:
        service = get_calendar_service(db)
        logger.info(f"Deleting event ID: {event_id}")
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        
        # Delete from local SQLite database if present
        try:
            local_event = db.query(CreatedEvent).filter(CreatedEvent.event_id == event_id).first()
            if local_event:
                db.delete(local_event)
                db.commit()
                logger.info("Deleted event reference from local database.")
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Could not remove event reference from local DB: {db_err}")
            
        return True
    except HttpError as e:
        logger.error(f"Google Calendar API delete error: {e}")
        raise RuntimeError(f"Google Calendar API deletion failure: {e.reason}")
    except PermissionError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error deleting event: {e}")
        raise e

def update_event(db: Session, event_id: str, update_data: dict) -> dict:
    """
    Updates an existing event's details (summary, start_time, end_time, etc.).
    Keeps unchanged fields intact.
    """
    try:
        service = get_calendar_service(db)
        logger.info(f"Fetching event {event_id} for update.")
        
        # Retrieve the current event resource first to keep unmodified fields
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        
        if "summary" in update_data and update_data["summary"]:
            event["summary"] = update_data["summary"]
        if "description" in update_data and update_data["description"]:
            event["description"] = update_data["description"]
        if "location" in update_data and update_data["location"]:
            event["location"] = update_data["location"]
            
        if "start_time" in update_data and update_data["start_time"]:
            event["start"] = {"dateTime": update_data["start_time"], "timeZone": "UTC"}
        if "end_time" in update_data and update_data["end_time"]:
            event["end"] = {"dateTime": update_data["end_time"], "timeZone": "UTC"}

        logger.info(f"Updating event ID: {event_id}")
        updated_event = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        
        # Update local SQLite database if present
        try:
            local_event = db.query(CreatedEvent).filter(CreatedEvent.event_id == event_id).first()
            if local_event:
                if "summary" in update_data and update_data["summary"]:
                    local_event.summary = update_data["summary"]
                if "start_time" in update_data and update_data["start_time"]:
                    local_event.start_time = parse_date_string(update_data["start_time"])
                if "end_time" in update_data and update_data["end_time"]:
                    local_event.end_time = parse_date_string(update_data["end_time"])
                db.commit()
                logger.info("Updated event reference in local database.")
        except Exception as db_err:
            db.rollback()
            logger.warning(f"Could not update event reference in local DB: {db_err}")

        # Extract start and end times format
        start_val = updated_event.get('start', {}).get('dateTime') or updated_event.get('start', {}).get('date', '')
        end_val = updated_event.get('end', {}).get('dateTime') or updated_event.get('end', {}).get('date', '')

        return {
            "id": updated_event.get("id"),
            "summary": updated_event.get("summary"),
            "start_time": start_val,
            "end_time": end_val,
            "html_link": updated_event.get("htmlLink"),
            "status": updated_event.get("status")
        }
    except HttpError as e:
        logger.error(f"Google Calendar API update error: {e}")
        raise RuntimeError(f"Google Calendar API update failure: {e.reason}")
    except PermissionError as e:
        raise e
    except Exception as e:
        logger.error(f"Unexpected error updating event: {e}")
        raise e

def search_events(db: Session, query: str) -> list:
    """
    Convenience method to search upcoming events. Uses list_events under the hood.
    """
    return list_events(db, query=query)
