# Google Calendar Service Documentation

This document describes the Google Calendar service integration for the pet grooming Discord bot. The service manages appointment scheduling with automatic availability checking and 1-hour slot management.

## Overview

The Google Calendar service provides:
- **Availability checking** - Verify if 1-hour slots are available
- **Appointment creation** - Book appointments with automatic conflict detection
- **Slot management** - Get all available slots for a given date
- **Appointment management** - View, update, and delete appointments

## Features

### 1. Automatic 1-Hour Slot Management
- All appointments are automatically set to 1-hour duration
- Prevents double-booking by checking for conflicts
- Supports custom business hours (default: 9 AM - 5 PM)

### 2. Smart Availability Checking
- Checks for existing events in the requested time slot
- Returns detailed conflict information
- Supports flexible time ranges

### 3. Appointment Creation with Validation
- Automatically validates availability before creating appointments
- Includes pet and customer information in event details
- Sets up automatic reminders (24 hours and 30 minutes before)

### 4. Business Logic Integration
- Seamlessly integrates with the existing pet grooming system
- Supports multiple service types
- Handles customer preferences and alternative time suggestions

## Setup Instructions

### 1. Google Cloud Project Setup

1. **Create a Google Cloud Project** (if you don't have one)
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select an existing one

2. **Enable Google Calendar API**
   - In the Google Cloud Console, go to "APIs & Services" > "Library"
   - Search for "Google Calendar API"
   - Click on it and press "Enable"

3. **Create Service Account**
   - Go to "APIs & Services" > "Credentials"
   - Click "Create Credentials" > "Service Account"
   - Fill in the service account details
   - Click "Create and Continue"

4. **Generate Service Account Key**
   - Click on the created service account
   - Go to "Keys" tab
   - Click "Add Key" > "Create New Key"
   - Choose JSON format
   - Download the credentials file

5. **Share Calendar with Service Account**
   - Copy the service account email from the credentials file
   - Go to Google Calendar settings
   - Find your calendar and click "Share with specific people"
   - Add the service account email with "Make changes to events" permission

### 2. Environment Configuration

1. **Place credentials file**
   - Save the downloaded JSON file as `credentials.json` in your project root
   - Add `credentials.json` to your `.gitignore` file

2. **Update environment variables**
   ```bash
   # Add to your .env file
   GOOGLE_CALENDAR_ID=primary
   # Or use a specific calendar ID from Google Calendar settings
   ```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## API Methods

### 1. Check Availability

```python
from google_calendar_service import google_calendar_service

# Check if a specific time slot is available
is_available, conflicting_events = google_calendar_service.check_availability(
    date="2024-01-15",
    start_time="10:00"
)

if is_available:
    print("Slot is available!")
else:
    print(f"Slot is booked. {len(conflicting_events)} conflicting events found.")
```

### 2. Create Appointment

```python
# Create a 1-hour appointment
event_id = google_calendar_service.create_appointment(
    date="2024-01-15",
    start_time="10:00",
    pet_name="Max",
    customer_name="John Smith",
    service_type="Full Grooming",
    notes="Golden Retriever, needs special attention to ears"
)

if event_id:
    print(f"Appointment created! Event ID: {event_id}")
else:
    print("Failed to create appointment - slot may be unavailable")
```

### 3. Get Available Slots

```python
# Get all available 1-hour slots for a day
available_slots = google_calendar_service.get_available_slots(
    date="2024-01-15",
    business_hours=("09:00", "17:00")  # 9 AM to 5 PM
)

print(f"Available times: {available_slots}")
# Output: ['09:00', '10:00', '11:00', '13:00', '14:00', '15:00', '16:00']
```

### 4. Manage Appointments

```python
# Get appointment details
details = google_calendar_service.get_appointment_details(event_id)
if details:
    print(f"Summary: {details.get('summary')}")
    print(f"Start: {details['start']['dateTime']}")
    print(f"Description: {details.get('description')}")

# Delete appointment
success = google_calendar_service.delete_appointment(event_id)
if success:
    print("Appointment deleted successfully")
```

## Business Logic Examples

### 1. Customer Booking Flow

```python
def book_appointment(customer_name, pet_name, preferred_date, preferred_time):
    """Complete booking flow with fallback options."""
    
    # Check if preferred time is available
    is_available, conflicts = google_calendar_service.check_availability(
        date=preferred_date,
        start_time=preferred_time
    )
    
    if is_available:
        # Book the preferred time
        event_id = google_calendar_service.create_appointment(
            date=preferred_date,
            start_time=preferred_time,
            pet_name=pet_name,
            customer_name=customer_name,
            service_type="Pet Grooming"
        )
        
        if event_id:
            return {
                "success": True,
                "message": f"Appointment booked for {preferred_date} at {preferred_time}",
                "event_id": event_id
            }
    
    # If preferred time not available, suggest alternatives
    available_slots = google_calendar_service.get_available_slots(
        date=preferred_date,
        business_hours=("09:00", "17:00")
    )
    
    if available_slots:
        return {
            "success": False,
            "message": f"Preferred time not available. Available times: {', '.join(available_slots[:3])}",
            "alternatives": available_slots
        }
    else:
        return {
            "success": False,
            "message": "No available times for this date"
        }
```

### 2. Staff Calendar Management

```python
def get_staff_schedule(date):
    """Get the complete schedule for a staff member on a given date."""
    
    # Get all events for the day
    available_slots = google_calendar_service.get_available_slots(
        date=date,
        business_hours=("09:00", "17:00")
    )
    
    # Calculate booked slots
    all_slots = ["09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    booked_slots = [slot for slot in all_slots if slot not in available_slots]
    
    return {
        "date": date,
        "available_slots": available_slots,
        "booked_slots": booked_slots,
        "total_slots": len(all_slots),
        "available_count": len(available_slots),
        "booked_count": len(booked_slots)
    }
```

## Integration with Discord Bot

### 1. Thread-Based Booking

```python
@bot.event
async def on_message(message):
    if isinstance(message.channel, discord.Thread) and not message.author.bot:
        # Check if message contains booking request
        if "book appointment" in message.content.lower():
            # Extract booking information from message
            # This is a simplified example
            booking_info = extract_booking_info(message.content)
            
            # Attempt to book appointment
            result = book_appointment(
                customer_name=booking_info["customer_name"],
                pet_name=booking_info["pet_name"],
                preferred_date=booking_info["date"],
                preferred_time=booking_info["time"]
            )
            
            # Send response to Discord thread
            if result["success"]:
                await message.channel.send(f"✅ {result['message']}")
            else:
                await message.channel.send(f"❌ {result['message']}")
```

### 2. Availability Commands

```python
@bot.command(name="check")
async def check_availability(ctx, date: str, time: str):
    """Check availability for a specific date and time."""
    
    is_available, conflicts = google_calendar_service.check_availability(date, time)
    
    if is_available:
        await ctx.send(f"✅ {date} at {time} is available!")
    else:
        await ctx.send(f"❌ {date} at {time} is not available.")
```

## Error Handling

The service includes comprehensive error handling:

### 1. Authentication Errors
- Invalid credentials
- Missing service account permissions
- Calendar access issues

### 2. API Errors
- Network connectivity issues
- Google API rate limits
- Invalid request parameters

### 3. Business Logic Errors
- Invalid date/time formats
- Conflicting appointments
- Missing required information

## Best Practices

### 1. Time Zone Handling
- All times are handled in UTC by default
- Consider implementing timezone conversion for local business hours
- Use consistent time formats (HH:MM)

### 2. Error Recovery
- Always check return values from service methods
- Implement retry logic for transient failures
- Log errors for debugging

### 3. Performance Optimization
- Cache frequently accessed availability data
- Batch operations when possible
- Use appropriate time ranges for queries

### 4. Security
- Never commit credentials to version control
- Use environment variables for sensitive data
- Regularly rotate service account keys

## Troubleshooting

### Common Issues

1. **"Service account not found" error**
   - Verify the credentials.json file exists
   - Check that the service account email is correct
   - Ensure the calendar is shared with the service account

2. **"Calendar not accessible" error**
   - Check calendar sharing permissions
   - Verify the calendar ID is correct
   - Ensure the service account has "Make changes to events" permission

3. **"Invalid time format" error**
   - Use HH:MM format for times (e.g., "14:30")
   - Use YYYY-MM-DD format for dates (e.g., "2024-01-15")
   - Ensure times are within business hours

4. **"Appointment creation failed" error**
   - Check if the time slot is already booked
   - Verify all required parameters are provided
   - Check for conflicting events

### Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service status:
```python
if google_calendar_service.service:
    print("Calendar service is properly configured")
else:
    print("Calendar service is not configured")
```

## Testing

Run the example file to test the service:
```bash
python calendar_example.py
```

This will run through various scenarios:
- Availability checking
- Appointment creation
- Slot management
- Error handling

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example files
3. Check the logs for detailed error messages
4. Verify your Google Calendar setup
5. Ensure all environment variables are properly configured
