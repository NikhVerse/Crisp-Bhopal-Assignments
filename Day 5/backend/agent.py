import json
from datetime import datetime
from sqlalchemy.orm import Session
from backend.config import settings
from backend.models import ChatHistory, ConversationLog
from backend.schemas import ChatResponse
from backend.weather import get_weather_data
from backend.calendar_tool import list_events, create_event, delete_event, update_event
from backend.llm import classify_intent, run_chat_completion
from backend.auth import get_auth_url
from backend.utils import logger

def get_session_history(db: Session, session_id: str, limit: int = 10) -> list:
    """
    Fetches the recent message history for the session to maintain conversational memory.
    """
    history = db.query(ChatHistory)\
        .filter(ChatHistory.session_id == session_id)\
        .order_by(ChatHistory.timestamp.asc())\
        .limit(limit)\
        .all()
        
    messages = []
    for msg in history:
        messages.append({"role": msg.role, "content": msg.content})
    return messages

def run_agent(db: Session, message: str, session_id: str) -> ChatResponse:
    """
    Main Agent Execution loop.
    1. Classifies intent & extracts arguments.
    2. Runs selected tool (Weather API, Google Calendar API).
    3. Merges tool data with conversational memory.
    4. Generates a natural AI response.
    5. Saves interaction logs to DB.
    """
    logger.info(f"Agent starting execution for message in session {session_id}")
    
    # 1. Intent Detection
    intent_info = classify_intent(message)
    intent = intent_info.get("intent", "general")
    params = intent_info.get("parameters", {})
    
    tool_called = None
    tool_data = None
    tool_error = None
    
    # 2. Tool Execution Routing
    try:
        if intent == "weather":
            city = params.get("city", "Delhi")
            tool_called = "get_weather_data"
            logger.info(f"Agent calling weather tool for city: {city}")
            tool_data = get_weather_data(city)
            
        elif intent == "calendar_create":
            tool_called = "create_calendar_event"
            logger.info(f"Agent calling create_event tool: {params}")
            tool_data = create_event(
                db=db,
                summary=params.get("summary", "New Event"),
                start_time=params.get("start_time"),
                end_time=params.get("end_time"),
                description=params.get("description"),
                location=params.get("location")
            )
            
        elif intent == "calendar_list":
            tool_called = "list_calendar_events"
            logger.info("Agent calling list_events tool")
            # Default list tomorrow/upcoming events
            tool_data = {
                "events": list_events(
                    db=db,
                    time_min=params.get("time_min"),
                    time_max=params.get("time_max"),
                    query=params.get("query")
                )
            }
            
        elif intent == "calendar_delete":
            tool_called = "delete_calendar_event"
            query = params.get("query")
            logger.info(f"Agent calling delete search for: {query}")
            
            # Find candidate events to delete
            upcoming = list_events(db=db, max_results=15)
            matching = [e for e in upcoming if query.lower() in e["summary"].lower()]
            
            if matching:
                target_event = matching[0]
                delete_event(db=db, event_id=target_event["id"])
                tool_data = {
                    "success": True,
                    "deleted_event": target_event,
                    "message": f"Deleted the event '{target_event['summary']}' scheduled for {target_event['start_time']}."
                }
            else:
                tool_data = {
                    "success": False,
                    "message": f"Could not find any upcoming calendar event matching: '{query}'."
                }
                
        elif intent == "calendar_update":
            tool_called = "update_calendar_event"
            query = params.get("query")
            update_data = params.get("update_data", {})
            logger.info(f"Agent calling update search for: {query} with {update_data}")
            
            # Find candidate events to update
            upcoming = list_events(db=db, max_results=15)
            matching = [e for e in upcoming if query.lower() in e["summary"].lower()]
            
            if matching:
                target_event = matching[0]
                updated_res = update_event(db=db, event_id=target_event["id"], update_data=update_data)
                tool_data = {
                    "success": True,
                    "original_event": target_event,
                    "updated_event": updated_res,
                    "message": f"Successfully updated '{target_event['summary']}'."
                }
            else:
                tool_data = {
                    "success": False,
                    "message": f"Could not find any upcoming calendar event matching: '{query}'."
                }
                
    except PermissionError as p_err:
        logger.warning(f"Google OAuth missing or expired: {p_err}")
        tool_error = "AUTH_REQUIRED"
        tool_data = {"error": "Google Calendar authentication is required.", "auth_url": get_auth_url()}
    except Exception as e:
        logger.error(f"Error executing tool ({tool_called}): {e}")
        tool_error = str(e)
        tool_data = {"error": tool_error}

    # 3. Conversational Memory Assembly
    history_messages = get_session_history(db, session_id)
    
    # Construct LLM system prompt context
    system_instruction = f"""
You are the AI Smart Personal Assistant.
Your objective is to generate a helpful, conversational response based on the user's message, current tool executions, and the chat history.

CURRENT RUNTIME ENVIRONMENT:
- Intent Detected: {intent}
- Tool Executed: {tool_called if tool_called else "None"}
- Tool Success: {"False" if tool_error else "True"}
- Tool Output Data: {json.dumps(tool_data) if tool_data else "None"}

INSTRUCTIONS FOR WRITING THE RESPONSE:
1. If the tool is 'get_weather_data' and was successful:
   - Provide a natural summary of the weather.
   - Present details (temperature, feels like, humidity, wind speed, condition).
   - End with a personalized, friendly "AI Recommendation" on what to wear or if outdoor activities are appropriate.
2. If Google Calendar authentication is required (AUTH_REQUIRED):
   - Politely tell the user they need to link their Google account.
   - Guide them to use the "Connect Calendar" button in the sidebar.
3. If a calendar tool was successful:
   - Formally confirm the action (create, delete, list, update).
   - Use dates and titles clearly. If listing events, print them in a clean, user-friendly checklist format.
4. If a calendar tool failed (with tool data error):
   - Explain the error contextually (e.g. "I couldn't find an event named X to delete").
5. Be concise, polite, helpful, and maintain a conversational persona.
"""

    messages = [
        {"role": "system", "content": system_instruction}
    ]
    
    # Add conversation history
    messages.extend(history_messages)
    
    # Add current user message
    messages.append({"role": "user", "content": message})
    
    # 4. Generate Final Response
    ai_response = run_chat_completion(messages)
    
    # 5. Log Chat History and Conversations to Database
    # Save User message
    user_chat = ChatHistory(session_id=session_id, role="user", content=message)
    db.add(user_chat)
    
    # Save Assistant message
    assistant_chat = ChatHistory(session_id=session_id, role="assistant", content=ai_response)
    db.add(assistant_chat)
    
    # Save Transaction log
    convo_log = ConversationLog(
        session_id=session_id,
        user_message=message,
        detected_intent=intent,
        tool_called=tool_called,
        tool_response=json.dumps(tool_data) if tool_data else (tool_error if tool_error else None),
        ai_response=ai_response
    )
    db.add(convo_log)
    db.commit()
    
    logger.info("Successfully updated chat history and logs in SQLite database.")
    
    return ChatResponse(
        response=ai_response,
        session_id=session_id,
        detected_intent=intent,
        tool_called=tool_called,
        tool_data=tool_data
    )
