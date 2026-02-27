import logging
from livekit.agents import function_tool, RunContext
import requests
from langchain_community.tools import DuckDuckGoSearchRun
import os
import smtplib
from email.mime.multipart import MIMEMultipart  
from email.mime.text import MIMEText
from typing import Optional, Annotated

@function_tool()
async def get_weather(
    context: RunContext,  # type: ignore
    city: str) -> str:
    """
    Get the current weather for a given city.
    """
    try:
        response = requests.get(
            f"https://wttr.in/{city}?format=3")
        if response.status_code == 200:
            logging.info(f"Weather for {city}: {response.text.strip()}")
            return response.text.strip()   
        else:
            logging.error(f"Failed to get weather for {city}: {response.status_code}")
            return f"Could not retrieve weather for {city}."
    except Exception as e:
        logging.error(f"Error retrieving weather for {city}: {e}")
        return f"An error occurred while retrieving weather for {city}." 

@function_tool()
async def search_web(
    context: RunContext,  # type: ignore
    query: str) -> str:
    """
    Search the web using DuckDuckGo.
    """
    try:
        results = DuckDuckGoSearchRun().run(tool_input=query)
        logging.info(f"Search results for '{query}': {results}")
        return results
    except Exception as e:
        logging.error(f"Error searching the web for '{query}': {e}")
        return f"An error occurred while searching the web for '{query}'."    

@function_tool()    
async def send_email(
    context: RunContext,  # type: ignore
    to_email: str,
    subject: str,
    message: str,
    cc_email: Optional[str] = None
) -> str:
    """
    Send an email through Gmail.
    
    Args:
        to_email: Recipient email address
        subject: Email subject line
        message: Email body content
        cc_email: Optional CC email address
    """
    try:
        # Gmail SMTP configuration
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        
        # Get credentials from environment variables
        gmail_user = os.getenv("GMAIL_USER")
        gmail_password = os.getenv("GMAIL_APP_PASSWORD")  # Use App Password, not regular password
        
        if not gmail_user or not gmail_password:
            logging.error("Gmail credentials not found in environment variables")
            return "Email sending failed: Gmail credentials not configured."
        
        # Create message
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # Add CC if provided
        recipients = [to_email]
        if cc_email:
            msg['Cc'] = cc_email
            recipients.append(cc_email)
        
        # Attach message body
        msg.attach(MIMEText(message, 'plain'))
        
        # Connect to Gmail SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()  # Enable TLS encryption
        server.login(gmail_user, gmail_password)
        
        # Send email
        text = msg.as_string()
        server.sendmail(gmail_user, recipients, text)
        server.quit()
        
        logging.info(f"Email sent successfully to {to_email}")
        return f"Email sent successfully to {to_email}"
        
    except smtplib.SMTPAuthenticationError:
        logging.error("Gmail authentication failed")
        return "Email sending failed: Authentication error. Please check your Gmail credentials."
    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
        return f"Email sending failed: SMTP error - {str(e)}"
    except Exception as e:
        logging.error(f"Error sending email: {e}")
        return f"An error occurred while sending email: {str(e)}"


# Simple in-memory calendar
class SimpleCalendar:
    """Simple in-memory calendar for testing"""
    def __init__(self):
        self.events = []
    
    def add_event(self, title, start, end, description=""):
        event = {
            'id': len(self.events) + 1,
            'title': title,
            'start': start,
            'end': end,
            'description': description
        }
        self.events.append(event)
        return event
    
    def list_events(self, start_date=None):
        if start_date:
            filtered = [e for e in self.events if e['start'] >= start_date]
            return filtered
        return self.events
    
    def delete_event(self, event_id):
        self.events = [e for e in self.events if e['id'] != event_id]
        return True


# Global calendar instance
_calendar = SimpleCalendar()


@function_tool()
async def manage_calendar(
    context: RunContext,  # type: ignore
    action: Annotated[str, "Action: 'list', 'create', or 'delete'"],
    start_date: Annotated[str, "Start date/time in format YYYY-MM-DD HH:MM"] = None,
    end_date: Annotated[str, "End date/time in format YYYY-MM-DD HH:MM"] = None,
    event_title: Annotated[str, "Title of the event"] = None,
    event_description: Annotated[str, "Description of the event"] = None,
    event_id: Annotated[int, "Event ID for deletion"] = None,
) -> str:
    """
    Manage calendar events: list upcoming events, create new events, or delete events.
    
    Examples:
    - List events: action='list'
    - Create event: action='create', start_date='2024-03-15 10:00', end_date='2024-03-15 11:00', event_title='Team Meeting'
    - Delete event: action='delete', event_id=1
    """
    try:
        if action == 'list':
            events = _calendar.list_events(start_date)
            if not events:
                return "No events found in your calendar."
            
            result = f"Found {len(events)} event(s):\n\n"
            for event in events:
                result += f"• Event ID {event['id']}: {event['title']}\n"
                result += f"  Start: {event['start']}\n"
                result += f"  End: {event['end']}\n"
                if event['description']:
                    result += f"  Description: {event['description']}\n"
                result += "\n"
            
            logging.info(f"Listed {len(events)} calendar events")
            return result
        
        elif action == 'create':
            if not event_title or not start_date or not end_date:
                return "Error: event_title, start_date, and end_date are required to create an event."
            
            event = _calendar.add_event(
                event_title, 
                start_date, 
                end_date, 
                event_description or ""
            )
            
            logging.info(f"Created calendar event: {event_title}")
            return f"Event created successfully!\n\nID: {event['id']}\nTitle: {event_title}\nStart: {start_date}\nEnd: {end_date}"
        
        elif action == 'delete':
            if event_id is None:
                return "Error: event_id is required to delete an event."
            
            _calendar.delete_event(event_id)
            logging.info(f"Deleted calendar event ID: {event_id}")
            return f"Event {event_id} deleted successfully."
        
        else:
            return f"Unknown action: {action}. Valid actions are: 'list', 'create', 'delete'"
    
    except Exception as e:
        logging.error(f"Error managing calendar: {e}")
        return f"An error occurred while managing the calendar: {str(e)}"
    