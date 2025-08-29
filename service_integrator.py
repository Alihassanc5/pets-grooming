"""
Service integration layer for connecting workflow nodes with Google Sheets and Calendar services.
This module provides enhanced functionality for booking appointments and managing data.
"""

import logging
import random
import string
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple

from google_sheet_service import goole_sheet_service
from google_calendar_service import google_calendar_service
from sheet_structures import SheetType
from workflow_state import ConversationState

logger = logging.getLogger('service_integrator')


class ServiceIntegrator:
    """
    Integration layer for Google Sheets and Calendar services.
    """
    
    def __init__(self):
        self.sheets_service = goole_sheet_service
        self.calendar_service = google_calendar_service
    
    def create_lead_record(self, state: ConversationState) -> bool:
        """
        Create a new lead record in Google Sheets.
        """
        try:
            lead_data = state.to_lead_record()
            success = self.sheets_service.insert_record(SheetType.LEADS, lead_data)
            
            if success:
                logger.info(f"Created lead record for {state.lead_id}")
            else:
                logger.warning(f"Failed to create lead record for {state.lead_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating lead record: {e}")
            return False
    
    def update_lead_record(self, state: ConversationState) -> bool:
        """
        Update an existing lead record.
        """
        try:
            lead_data = state.to_lead_record()
            success = self.sheets_service.update_record(
                SheetType.LEADS,
                state.lead_id,
                lead_data
            )
            
            if success:
                logger.info(f"Updated lead record for {state.lead_id}")
            else:
                logger.warning(f"Failed to update lead record for {state.lead_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error updating lead record: {e}")
            return False
    
    def create_or_update_pet_record(self, state: ConversationState) -> bool:
        """
        Create a new pet record or update existing one.
        """
        try:
            # Generate pet ID if not exists
            if not state.pet_id:
                state.pet_id = "PET" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            pet_data = state.to_pet_record()
            
            # Check if pet record exists
            existing_record = self.sheets_service.get_record(SheetType.PETS, state.lead_id)
            
            if existing_record:
                # Update existing record
                success = self.sheets_service.update_record(
                    SheetType.PETS,
                    state.lead_id,
                    pet_data
                )
                logger.info(f"Updated pet record for {state.lead_id}")
            else:
                # Create new record
                success = self.sheets_service.insert_record(SheetType.PETS, pet_data)
                logger.info(f"Created pet record for {state.lead_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error creating/updating pet record: {e}")
            return False
    
    def get_available_services(self) -> List[Dict[str, Any]]:
        """
        Get all available services from the Services sheet.
        """
        try:
            services = self.sheets_service.get_all_records(SheetType.SERVICES)
            logger.info(f"Retrieved {len(services)} services")
            return services
            
        except Exception as e:
            logger.error(f"Error retrieving services: {e}")
            return []
    
    def get_service_by_id(self, service_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific service by ID.
        """
        try:
            services = self.get_available_services()
            for service in services:
                if service.get('service_id') == service_id:
                    return service
            
            logger.warning(f"Service not found: {service_id}")
            return None
            
        except Exception as e:
            logger.error(f"Error retrieving service {service_id}: {e}")
            return None
    
    def get_brand_info(self) -> Optional[Dict[str, Any]]:
        """
        Get brand/business information from the Brands sheet.
        """
        return self.sheets_service.get_all_records(SheetType.BRANDS)
    
    def check_calendar_availability(self, date: str, start_time: str) -> Tuple[bool, str]:
        """
        Check if a time slot is available in the calendar.
        
        Args:
            date: Date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
        
        Returns:
            Tuple of (is_available, message)
        """
        try:
            is_available, message = self.calendar_service._check_availability(date, start_time)
            logger.info(f"Availability check for {date} {start_time}: {is_available}")
            return is_available, message
            
        except Exception as e:
            logger.error(f"Error checking calendar availability: {e}")
            return False, "Error checking availability"
    
    def create_appointment(self, state: ConversationState, date: str, start_time: str, 
                          service_info: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Create an appointment in both Google Calendar and Sheets.
        
        Args:
            state: Current conversation state
            date: Appointment date in YYYY-MM-DD format
            start_time: Start time in HH:MM format
            service_info: Service information dictionary
        
        Returns:
            Tuple of (success, message/event_id)
        """
        try:
            # Create calendar event
            success, event_id = self.calendar_service.create_appointment(
                date=date,
                start_time=start_time,
                pet_name=state.pet_name or "Pet",
                customer_name=state.customer_name or "Customer",
                service_type=service_info.get('title', 'Pet Grooming'),
                notes=f"Pet: {state.pet_name}, Breed: {state.breed}, Weight: {state.weight_kg}kg"
            )
            
            if success:
                # Generate appointment ID
                state.appointment_id = "APT" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                state.service_id = service_info.get('service_id', '')
                state.appointment_date = date
                state.appointment_time = start_time
                state.total_price = service_info.get('base_price', 0)
                
                # Create appointment record in sheets
                appointment_data = state.to_appointment_record()
                sheets_success = self.sheets_service.insert_record(SheetType.APPOINTMENTS, appointment_data)
                
                if sheets_success:
                    # Update lead status to booked
                    state.update_status("booked")
                    self.update_lead_record(state)
                    
                    logger.info(f"Successfully created appointment {state.appointment_id}")
                    return True, event_id
                else:
                    logger.warning("Calendar event created but failed to save to sheets")
                    return True, event_id
            else:
                logger.error(f"Failed to create calendar event: {event_id}")
                return False, event_id
                
        except Exception as e:
            logger.error(f"Error creating appointment: {e}")
            return False, str(e)
    
    def get_suggested_time_slots(self, days_ahead: int = 7) -> List[Dict[str, str]]:
        """
        Get suggested available time slots for the next few days.
        
        Args:
            days_ahead: Number of days to look ahead
        
        Returns:
            List of available time slots
        """
        suggested_slots = []
        
        try:
            # Define business hours (9 AM to 5 PM)
            business_hours = [
                "09:00", "10:00", "11:00", "12:00",
                "13:00", "14:00", "15:00", "16:00"
            ]
            
            # Check next few days (skip Sundays)
            current_date = datetime.now()
            for i in range(1, days_ahead + 1):
                check_date = current_date + timedelta(days=i)
                
                # Skip Sundays (weekday 6)
                if check_date.weekday() == 6:
                    continue
                
                date_str = check_date.strftime("%Y-%m-%d")
                
                # Check each business hour
                for hour in business_hours:
                    is_available, _ = self.check_calendar_availability(date_str, hour)
                    
                    if is_available:
                        suggested_slots.append({
                            "date": date_str,
                            "time": hour,
                            "day_name": check_date.strftime("%A"),
                            "formatted_date": check_date.strftime("%B %d, %Y")
                        })
                    
                    # Limit to 6 suggestions to avoid overwhelming
                    if len(suggested_slots) >= 6:
                        break
                
                if len(suggested_slots) >= 6:
                    break
            
            logger.info(f"Found {len(suggested_slots)} available time slots")
            return suggested_slots
            
        except Exception as e:
            logger.error(f"Error getting suggested time slots: {e}")
            return []
    
    def calculate_service_price(self, service_info: Dict[str, Any], 
                              pet_breed: str, pet_weight: float) -> float:
        """
        Calculate the final price for a service based on pet characteristics.
        
        Args:
            service_info: Service information from sheets
            pet_breed: Pet breed
            pet_weight: Pet weight in kg
        
        Returns:
            Calculated price
        """
        try:
            base_price = float(service_info.get('base_price', 0))
            
            # For now, just return base price
            # TODO: Implement breed modifiers and weight brackets from JSON fields
            
            return base_price
            
        except Exception as e:
            logger.error(f"Error calculating service price: {e}")
            return 0.0


# Create global instance
service_integrator = ServiceIntegrator()
