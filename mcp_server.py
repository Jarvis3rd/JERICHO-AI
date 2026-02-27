from dotenv import load_dotenv
load_dotenv()

import asyncio
import os
import requests
import resend
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from mcp.server.fastmcp import FastMCP
from google_calendar import _get_calendar_service
from datetime import datetime, timedelta

resend.api_key = os.getenv("RESEND_API_KEY")

mcp = FastMCP("Jericho")

# ── Weather ──────────────────────────────────────────────────────────────────
@mcp.tool()
def get_weather(city: str) -> str:
    """Get current weather for a city."""
    try:
        response = requests.get(f"https://wttr.in/{city}?format=3")
        return response.text.strip()
    except Exception as e:
        return f"Error getting weather: {e}"

# ── Web Search ───────────────────────────────────────────────────────────────
@mcp.tool()
def search_web(query: str) -> str:
    """Search the web using DuckDuckGo."""
    try:
        from langchain_community.tools import DuckDuckGoSearchRun
        return DuckDuckGoSearchRun().run(tool_input=query)
    except Exception as e:
        return f"Error searching: {e}"

# ── Email ────────────────────────────────────────────────────────────────────
@mcp.tool()
def send_email(to_email: str, subject: str, message: str) -> str:
    """Send an email via Gmail."""
    try:
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.sendmail(gmail_user, to_email, msg.as_string())
        server.quit()
        return f"Email sent to {to_email}"
    except Exception as e:
        return f"Error sending email: {e}"

# ── SMS ──────────────────────────────────────────────────────────────────────
@mcp.tool()
def send_sms(message: str, to_number: str = None, carrier: str = "xfinity") -> str:
    """Send SMS to any US carrier."""
    try:
        number = to_number if to_number else os.getenv("YOUR_PHONE_NUMBER")
        phone_digits = number.replace("+1", "").replace("-", "").replace(" ", "")
        gateways = {
            "xfinity": "vtext.com", "verizon": "vtext.com",
            "att": "txt.att.net", "tmobile": "tmomail.net",
        }
        gateway = gateways.get(carrier.lower(), "vtext.com")
        resend.Emails.send({
            "from": "jericho@apertureautomations.ai",
            "to": f"{phone_digits}@{gateway}",
            "subject": " ",
            "text": message
        })
        return f"SMS sent to {phone_digits}"
    except Exception as e:
        return f"Error sending SMS: {e}"

# ── Google Calendar ───────────────────────────────────────────────────────────
@mcp.tool()
def list_calendar_events(days_ahead: int = 7) -> str:
    """List upcoming Google Calendar events."""
    try:
        service = _get_calendar_service()
        now = datetime.utcnow().isoformat() + "Z"
        future = (datetime.utcnow() + timedelta(days=days_ahead)).isoformat() + "Z"
        events = service.events().list(
            calendarId="primary", timeMin=now, timeMax=future,
            maxResults=20, singleEvents=True, orderBy="startTime"
        ).execute().get("items", [])
        if not events:
            return f"No events in next {days_ahead} days."
        result = ""
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date"))
            result += f"- {e.get('summary', 'No title')} at {start}\n"
        return result
    except Exception as e:
        return f"Error listing events: {e}"

@mcp.tool()
def create_calendar_event(title: str, start: str, end: str, description: str = "") -> str:
    """Create a Google Calendar event. Start/end format: 2026-02-25T10:00:00"""
    try:
        service = _get_calendar_service()
        event = service.events().insert(calendarId="primary", body={
            "summary": title,
            "description": description,
            "start": {"dateTime": start, "timeZone": "America/Los_Angeles"},
            "end": {"dateTime": end, "timeZone": "America/Los_Angeles"},
        }).execute()
        return f"Event created: {title} (ID: {event['id']})"
    except Exception as e:
        return f"Error creating event: {e}"

# ── Run server ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()