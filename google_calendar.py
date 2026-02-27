import os
import logging
from datetime import datetime, timedelta
from typing import Optional, Annotated
from livekit.agents import function_tool, RunContext
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ["https://www.googleapis.com/auth/calendar"]
CREDENTIALS_FILE = os.path.join(os.path.dirname(__file__), "credentials.json")
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "token.json")

def _get_calendar_service():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

@function_tool()
async def manage_google_calendar(
    context: RunContext,
    action: Annotated[str, "Action: list, create, delete, or update"],
    event_title: Annotated[Optional[str], "Title of the event"] = None,
    start_datetime: Annotated[Optional[str], "Start: YYYY-MM-DDTHH:MM:SS"] = None,
    end_datetime: Annotated[Optional[str], "End: YYYY-MM-DDTHH:MM:SS"] = None,
    description: Annotated[Optional[str], "Event description"] = None,
    location: Annotated[Optional[str], "Event location"] = None,
    event_id: Annotated[Optional[str], "Event ID for delete or update"] = None,
    days_ahead: Annotated[int, "For list: how many days ahead to look"] = 7,
) -> str:
    """Manage Lloyd's Google Calendar. List, create, delete, or update events."""
    try:
        service = _get_calendar_service()
        if action == "list":
            now = datetime.utcnow().isoformat() + "Z"
            future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
            events_result = service.events().list(
                calendarId="primary", timeMin=now, timeMax=future,
                maxResults=20, singleEvents=True, orderBy="startTime",
            ).execute()
            events = events_result.get("items", [])
            if not events:
                return f"No events found in the next {days_ahead} days."
            result = f"You have {len(events)} events in the next {days_ahead} days:\n\n"
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                result += f"- {event.get('summary', 'No title')}\n"
                result += f"  Start: {start}\n"
                if event.get("location"):
                    result += f"  Location: {event['location']}\n"
                result += f"  ID: {event['id']}\n\n"
            return result
        elif action == "create":
            if not event_title or not start_datetime or not end_datetime:
                return "Error: event_title, start_datetime, and end_datetime are required."
            event_body = {
                "summary": event_title,
                "start": {"dateTime": start_datetime, "timeZone": "America/Los_Angeles"},
                "end": {"dateTime": end_datetime, "timeZone": "America/Los_Angeles"},
            }
            if description:
                event_body["description"] = description
            if location:
                event_body["location"] = location
            event = service.events().insert(calendarId="primary", body=event_body).execute()
            return f"Event created!\nTitle: {event_title}\nStart: {start_datetime}\nID: {event['id']}"
        elif action == "delete":
            if not event_id:
                return "Error: event_id is required. Use list first to find it."
            service.events().delete(calendarId="primary", eventId=event_id).execute()
            return f"Event {event_id} deleted successfully."
        elif action == "update":
            if not event_id:
                return "Error: event_id is required. Use list first to find it."
            event = service.events().get(calendarId="primary", eventId=event_id).execute()
            if event_title:
                event["summary"] = event_title
            if start_datetime:
                event["start"] = {"dateTime": start_datetime, "timeZone": "America/Los_Angeles"}
            if end_datetime:
                event["end"] = {"dateTime": end_datetime, "timeZone": "America/Los_Angeles"}
            if description:
                event["description"] = description
            if location:
                event["location"] = location
            updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
            return f"Event updated!\nTitle: {updated.get('summary')}\nID: {event_id}"
        else:
            return f"Unknown action: {action}. Valid: list, create, delete, update"
    except HttpError as e:
        logging.error(f"Google Calendar API error: {e}")
        return f"Google Calendar error: {str(e)}"
    except Exception as e:
        logging.error(f"Error: {e}")
        return f"An error occurred: {str(e)}"