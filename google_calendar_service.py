"""
Google Calendar service for managing appointments in the pet grooming system.
This service checks calendar availability and creates appointments for 1-hour slots.
"""

import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_CALENDAR_CREDENTIALS_FILE

logger = logging.getLogger('google_calendar_service')

class GoogleCalendarService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.calendar_id = 'primary'
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Calendar API using service account credentials."""
        try:
            # Define the scope for Calendar API
            scope = ['https://www.googleapis.com/auth/calendar']
            
            creds = None
            # token.json stores the user's access and refresh tokens
            if os.path.exists('token.json'):
                creds = Credentials.from_authorized_user_file('token.json', scope)
                
            # If no valid credentials, let user log in
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        GOOGLE_CALENDAR_CREDENTIALS_FILE, scope)
                    creds = flow.run_local_server(port=0)  # opens a browser for auth
                # Save credentials
                
                with open('token.json', 'w') as token:
                    token.write(creds.to_json())
            
            self.service = build('calendar', 'v3', credentials=creds)
            logger.info("Successfully authenticated with Google Calendar API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Calendar API: {e}")
    
    def _check_availability(self, date: str, start_time: str, end_time: str = None) -> Tuple[bool, str]:
        """
        Check if a 1-hour slot is available on the specified date and time.
        
        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format (24-hour)
            end_time: End time in HH:MM format (optional, defaults to 1 hour after start_time)
        
        Returns:
            Tuple of (is_available, conflicting_events)
        """
        if not self.service:
            logger.warning("Google Calendar service not available.")
            return False, []
        
        try:
            # Parse date and time
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            
            # If no end_time provided, make it 1 hour after start_time
            if end_time is None:
                end_datetime = start_datetime + timedelta(hours=1)
            else:
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            # Convert to RFC3339 format for Google Calendar API
            time_min = start_datetime.isoformat() + 'Z'
            time_max = end_datetime.isoformat() + 'Z'
            
            # Query for events in the time range
            events_result = self.service.events().list(
                calendarId=self.calendar_id,
                timeMin=time_min,
                timeMax=time_max,
            ).execute()
            
            events = events_result.get('items', [])
            
            # Check if there are any conflicting events
            if events:
                logger.info(f"Found {len(events)} conflicting events for {date} {start_time}")
                return False, "This timeslot is not available"
            else:
                logger.info(f"Slot available for {date} {start_time}")
                return True, "This timeslot is available"
                
        except HttpError as e:
            logger.error(f"HTTP error occurred while checking availability: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error checking availability: {e}")
            return False, str(e)
    
    def create_appointment(self, 
                          date: str, 
                          start_time: str, 
                          pet_name: str, 
                          customer_name: str, 
                          service_type: str = "Pet Grooming",
                          notes: str = "",
                          end_time: str = None) -> Optional[str]:
        """
        Create a 1-hour appointment in Google Calendar.
        
        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format (24-hour)
            pet_name: Name of the pet
            customer_name: Name of the customer
            service_type: Type of service (default: "Pet Grooming")
            notes: Additional notes
            end_time: End time in HH:MM format (optional, defaults to 1 hour after start_time)
        
        Returns:
            Event ID if successful, None otherwise
        """
        if not self.service:
            logger.warning("Google Calendar service not available.")
            return False, "Google Calendar service not available."
        
        try:
            # First check availability
            is_available, message = self._check_availability(date, start_time, end_time)
            
            if not is_available:
                logger.warning(message)
                return False, message
            
            # Parse date and time
            start_datetime = datetime.strptime(f"{date} {start_time}", "%Y-%m-%d %H:%M")
            
            # If no end_time provided, make it 1 hour after start_time
            if end_time is None:
                end_datetime = start_datetime + timedelta(hours=1)
            else:
                end_datetime = datetime.strptime(f"{date} {end_time}", "%Y-%m-%d %H:%M")
            
            # Create event
            event = {
                'summary': f"{service_type} - {pet_name}",
                'description': f"Customer: {customer_name}\nPet: {pet_name}\nService: {service_type}\n\nNotes: {notes}",
                'start': {
                    'dateTime': start_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': end_datetime.isoformat(),
                    'timeZone': 'UTC',
                },
                'reminders': {
                    'useDefault': False,
                    'overrides': [
                        {'method': 'email', 'minutes': 24 * 60},  # 1 day before
                        {'method': 'popup', 'minutes': 30},       # 30 minutes before
                    ],
                },
            }
            
            # Insert the event
            event_result = self.service.events().insert(
                calendarId=self.calendar_id,
                body=event
            ).execute()
            
            event_id = event_result.get('id')
            logger.info(f"Successfully created appointment: {event_id}")
            return True, event_id
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while creating appointment: {e}")
            return False, str(e)
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return False, str(e) 
    
    def get_appointment_details(self, event_id: str) -> Optional[Dict]:
        """
        Get details of a specific appointment.
        
        Args:
            event_id: The ID of the event
        
        Returns:
            Dict with appointment details or None if not found
        """
        if not self.service:
            logger.warning("Google Calendar service not available.")
            return None
        
        try:
            event = self.service.events().get(
                calendarId=self.calendar_id,
                eventId=event_id
            ).execute()
            
            return event
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while getting appointment details: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting appointment details: {e}")
            return None

# Create a global instance
google_calendar_service = GoogleCalendarService()
