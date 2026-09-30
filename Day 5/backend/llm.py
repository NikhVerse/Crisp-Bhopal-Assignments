import os
import json
from datetime import datetime
from backend.config import settings
from backend.utils import logger

# Try to initialize Groq client
groq_client = None
if settings.GROQ_API_KEY:
    try:
        from groq import Groq
        groq_client = Groq(api_key=settings.GROQ_API_KEY)
        logger.info("Groq client initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Groq client: {e}")

# Try to initialize Gemini client
gemini_model = None
if settings.GEMINI_API_KEY:
    try:
        import google.generativeai as genai
        genai.configure(api_key=settings.GEMINI_API_KEY)
        gemini_model = genai.GenerativeModel('gemini-1.5-flash')
        logger.info("Gemini client initialized successfully.")
    except Exception as e:
        logger.error(f"Error initializing Gemini client: {e}")

def get_current_time_context() -> str:
    """
    Returns a string containing the current date and time for LLM reference.
    """
    now = datetime.now()
    return now.strftime("Current reference time is %A, %B %d, %Y, %I:%M %p (ISO format: %Y-%m-%dT%H:%M:%S)")

def get_llm_provider() -> str:
    """
    Determines which provider to use based on settings and key availability.
    """
    provider = settings.LLM_PROVIDER
    if provider == "groq" and groq_client:
        return "groq"
    elif provider == "gemini" and gemini_model:
        return "gemini"
    # Fallback checks
    if groq_client:
        return "groq"
    if gemini_model:
        return "gemini"
    return "mock"

def run_chat_completion(messages: list) -> str:
    """
    Sends a list of messages to the configured LLM provider.
    Returns the string completion.
    """
    provider = get_llm_provider()
    logger.info(f"Running chat completion using provider: {provider}")

    if provider == "groq":
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                temperature=0.7,
                max_tokens=1024
            )
            return chat_completion.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq chat completion failed: {e}. Trying Gemini fallback if available.")
            if gemini_model:
                return _run_gemini_chat(messages)
            
    elif provider == "gemini":
        return _run_gemini_chat(messages)

    # Mock Fallback
    logger.warning("No LLM API keys provided or LLM calls failed. Using mock response.")
    last_user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            last_user_msg = m.get("content", "")
            break
    return mock_general_chat(last_user_msg)

def _run_gemini_chat(messages: list) -> str:
    """Helper to run chat completion via Google Generative AI SDK."""
    try:
        # Convert OpenAI-like message history to Gemini format or plain text
        prompt = ""
        for msg in messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            prompt += f"{role}: {msg['content']}\n\n"
        prompt += "Assistant: "
        
        response = gemini_model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Gemini chat completion failed: {e}")
        return "I encountered an error communicating with the AI service. Please verify your API settings."

def classify_intent(message: str) -> dict:
    """
    Classifies user message intent and extracts parameters into structured JSON.
    Returns dictionary with keys: 'intent' and 'parameters'.
    """
    provider = get_llm_provider()
    time_ctx = get_current_time_context()
    
    system_prompt = f"""
You are an expert NLP classifier for a smart assistant. Your job is to classify the user's intent and extract arguments.
{time_ctx}

You MUST classify the query into one of these intents:
1. "weather" - User wants to know current weather or temperature.
   Parameters:
     - "city" (string, required): Extracted city name. Must resolve to a standard English name (e.g. "Delhi", "Mumbai", "London").
2. "calendar_create" - User wants to schedule, book, create, or add a meeting/event/reminder.
   Parameters:
     - "summary" (string, required): Concise title (e.g. "Dentist Appointment", "Meeting with John").
     - "start_time" (string, required): Start date-time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS) resolved using the current reference time.
     - "end_time" (string, required): End date-time in ISO 8601 format (YYYY-MM-DDTHH:MM:SS). If end time is not specified, default to exactly 1 hour after start_time.
     - "description" (string, optional): Details of event.
     - "location" (string, optional): Meeting location.
3. "calendar_list" - User wants to view, show, list, check their calendar/upcoming events/meetings.
   Parameters:
     - "time_min" (string, optional): ISO 8601 start time to filter.
     - "time_max" (string, optional): ISO 8601 end time to filter.
     - "query" (string, optional): Filter events containing a specific keyword.
4. "calendar_delete" - User wants to delete, remove, cancel a meeting/event.
   Parameters:
     - "query" (string, required): Search query to locate the event (e.g. "dentist", "alice").
5. "calendar_update" - User wants to reschedule, modify, change, or update a meeting.
   Parameters:
     - "query" (string, required): Search query to locate the target event to change (e.g. "coffee").
     - "update_data" (object, required): A JSON object with optional parameters to update: 'summary', 'start_time' (ISO 8601), 'end_time' (ISO 8601), 'description', 'location'.
6. "general" - Simple greetings, chitchat, or requests unrelated to weather or calendar tools.

IMPORTANT DATE/TIME GUIDELINES:
- Parse relative dates like "tomorrow 5 PM", "next Monday 7 PM", "Friday 4 PM" or "today" relative to the reference time.
- Resolve exact years, months, and days based on the reference time: {time_ctx}.
- Ensure start_time and end_time are valid ISO 8601 strings (without timezone offset unless specified).

You MUST respond with a single, clean JSON object. Do not include markdown code block syntax (like ```json) in your raw output. Ensure it matches this schema:
{{
  "intent": "intent_name",
  "parameters": {{ ... }}
}}
"""

    logger.info(f"Classifying intent for: '{message}' using {provider}")

    if provider == "groq":
        try:
            chat_completion = groq_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": message}
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.1, # low temperature for deterministic intent extraction
                response_format={"type": "json_object"}
            )
            raw_content = chat_completion.choices[0].message.content.strip()
            return json.loads(raw_content)
        except Exception as e:
            logger.error(f"Groq intent classification failed: {e}. Trying Gemini...")
            if gemini_model:
                return _classify_intent_gemini(system_prompt, message)

    elif provider == "gemini":
        return _classify_intent_gemini(system_prompt, message)

    # Fallback to Mock / Rule-based
    logger.warning("Using mock keyword-based intent classification.")
    return mock_intent_classifier(message)

def _classify_intent_gemini(system_prompt: str, message: str) -> dict:
    """Helper to classify intent using Google Gemini SDK."""
    try:
        combined_prompt = f"{system_prompt}\n\nUser Message: {message}\n\nJSON Output:"
        response = gemini_model.generate_content(combined_prompt)
        text = response.text.strip()
        
        # Strip markdown json blocks if returned
        if text.startswith("```"):
            text = text.replace("```json", "").replace("```", "").strip()
            
        return json.loads(text)
    except Exception as e:
        logger.error(f"Gemini intent classification failed: {e}")
        return mock_intent_classifier(message)

def mock_intent_classifier(message: str) -> dict:
    """
    Fallback keyword parsing when LLM API keys are not active.
    """
    msg = message.lower()
    
    # Check Weather
    if any(k in msg for k in ["weather", "temperature", "temp", "rain", "snow", "wind", "picnic"]):
        # Simple extraction
        words = message.split()
        city = "Delhi"
        for i, word in enumerate(words):
            if word.lower() in ["in", "at"] and i + 1 < len(words):
                city = words[i+1].strip("?.,!")
                break
        return {
            "intent": "weather",
            "parameters": {"city": city}
        }
    
    # Check Calendar Create
    if any(k in msg for k in ["create", "schedule", "book", "add a meeting", "dentist", "appointment", "reminder"]):
        summary = "Meeting"
        if "dentist" in msg:
            summary = "Dentist Appointment"
        elif "doctor" in msg:
            summary = "Doctor Appointment"
        elif "gym" in msg:
            summary = "Gym Session"
        elif "meeting with" in msg:
            parts = msg.split("meeting with")
            if len(parts) > 1:
                summary = f"Meeting with {parts[1].split()[0].capitalize()}"
        
        tomorrow = (datetime.utcnow() + (datetime.now() - datetime.utcnow())).replace(hour=17, minute=0, second=0, microsecond=0)
        # Default start to tomorrow at 5 PM local
        start_time = tomorrow.isoformat()
        end_time = tomorrow.replace(hour=18).isoformat()
        
        return {
            "intent": "calendar_create",
            "parameters": {
                "summary": summary,
                "start_time": start_time,
                "end_time": end_time,
                "description": "Scheduled via Smart Assistant fallback rules"
            }
        }

    # Check Calendar List
    if any(k in msg for k in ["show", "list", "upcoming", "meetings", "calendar", "events", "plans"]):
        return {
            "intent": "calendar_list",
            "parameters": {}
        }

    # Check Calendar Delete
    if any(k in msg for k in ["delete", "remove", "cancel"]):
        # Extract query search string
        query = "meeting"
        words = msg.split()
        for w in ["meeting", "appointment", "session", "dentist", "doctor"]:
            if w in words:
                query = w
        return {
            "intent": "calendar_delete",
            "parameters": {"query": query}
        }
        
    return {
        "intent": "general",
        "parameters": {}
    }

def mock_general_chat(message: str) -> str:
    """
    Offline mock response dictionary.
    """
    msg = message.lower()
    if "hello" in msg or "hi" in msg:
        return "Hello! I am your AI Smart Personal Assistant. How can I help you today? I can check the weather (try asking 'What is the weather in Delhi?') or coordinate your Google Calendar (try 'Show upcoming events')."
    if "who are you" in msg:
        return "I am a smart AI personal assistant. I can query weather stats using OpenWeatherMap and manage your agenda via Google Calendar."
    return f"I received: '{message}'. Note: I'm currently running in local demonstration mode. Please add your API keys to `.env` to unlock my full capabilities!"
