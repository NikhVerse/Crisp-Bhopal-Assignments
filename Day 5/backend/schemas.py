from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# Chat schemas
class ChatRequest(BaseModel):
    message: str = Field(..., description="The user's query or instruction.")
    session_id: str = Field(..., description="Unique conversation session identifier.")

class ChatResponse(BaseModel):
    response: str = Field(..., description="The AI's natural language response.")
    session_id: str = Field(..., description="The session identifier.")
    detected_intent: Optional[str] = Field(None, description="The detected intent.")
    tool_called: Optional[str] = Field(None, description="The tool that was executed, if any.")
    tool_data: Optional[Dict[str, Any]] = Field(None, description="Data returned from the tool execution.")

# Weather schemas
class WeatherInfo(BaseModel):
    city: str
    temperature: float
    feels_like: float
    humidity: int
    pressure: int
    visibility: int
    wind_speed: float
    sunrise: str
    sunset: str
    clouds: int
    condition: str
    description: str
    icon: str
    ai_recommendation: Optional[str] = None

# Calendar schemas
class CalendarEventCreate(BaseModel):
    summary: str = Field(..., description="Title of the meeting/event.")
    start_time: str = Field(..., description="ISO 8601 start time (e.g. 2026-07-27T10:00:00).")
    end_time: str = Field(..., description="ISO 8601 end time (e.g. 2026-07-27T11:00:00).")
    description: Optional[str] = Field(None, description="Event description.")
    location: Optional[str] = Field(None, description="Event location.")
    recurrence: Optional[str] = Field(None, description="Optional RRULE string (e.g. RRULE:FREQ=WEEKLY;BYDAY=MO).")

class CalendarEventUpdate(BaseModel):
    summary: Optional[str] = None
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None

class CalendarEventResponse(BaseModel):
    id: str
    summary: str
    start_time: str
    end_time: str
    html_link: Optional[str] = None
    status: str

# Auth schemas
class AuthStatus(BaseModel):
    is_connected: bool
    email: Optional[str] = None
    auth_url: Optional[str] = None
