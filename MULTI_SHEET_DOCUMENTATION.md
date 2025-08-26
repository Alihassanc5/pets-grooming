# Multi-Sheet Google Sheets System Documentation

This document describes the comprehensive multi-sheet Google Sheets system for the pet grooming Discord bot. The system can handle multiple sheet types, each with their own structure and validation rules.

## Overview

The system consists of three main components:

1. **Sheet Structures** (`sheet_structures.py`) - Defines the structure and validation rules for each sheet type
2. **Multi-Sheet Service** (`multi_sheet_service.py`) - Handles all CRUD operations for different sheet types
3. **Discord Bot Integration** - Uses the service to manage data when threads are created

## Sheet Types

The system supports five different sheet types, each designed for specific business needs:

### 1. Pets Sheet
**Purpose**: Track pet information and grooming history
**Key Fields**:
- `lead_id` (required) - Discord thread ID
- `pet_id` (auto-generated) - Unique pet identifier
- `status` - Current status (initiated, in_progress, completed, etc.)
- `pet_name` - Pet's name
- `species` - Pet species (Dog, Cat, etc.)
- `breed` - Pet breed
- `weight_kg` - Weight in kilograms
- `age_years` - Age in years
- `coat_condition` - Current coat condition
- `notes` - Additional notes

### 2. Leads Sheet
**Purpose**: Track customer leads and contact information
**Key Fields**:
- `lead_id` (required) - Unique lead identifier
- `customer_name` - Customer's full name
- `phone` - Contact phone number
- `email` - Contact email address
- `address` - Customer address
- `status` - Lead status (new, contacted, qualified, etc.)
- `source` - Lead source (website, referral, etc.)
- `created_date` (auto-generated) - Date lead was created
- `notes` - Additional notes

### 3. Services Sheet
**Purpose**: Manage available grooming services
**Key Fields**:
- `service_id` (auto-generated) - Unique service identifier
- `service_name` (required) - Name of the service
- `description` - Service description
- `price` (required) - Service price
- `duration_minutes` - Estimated duration
- `category` - Service category
- `is_active` - Whether service is currently available

### 4. Appointments Sheet
**Purpose**: Schedule and track grooming appointments
**Key Fields**:
- `appointment_id` (auto-generated) - Unique appointment identifier
- `lead_id` (required) - Reference to lead
- `pet_id` (required) - Reference to pet
- `service_id` (required) - Reference to service
- `appointment_date` (required) - Appointment date
- `appointment_time` (required) - Appointment time
- `status` - Appointment status (scheduled, in_progress, completed, etc.)
- `groomer_name` - Assigned groomer
- `notes` - Appointment notes
- `total_price` - Total price for the appointment

### 5. Brands Sheet
**Purpose**: Track product brands and suppliers
**Key Fields**:
- `brand_id` (auto-generated) - Unique brand identifier
- `brand_name` (required) - Brand name
- `description` - Brand description
- `website` - Brand website
- `contact_email` - Contact email
- `is_active` - Whether brand is active

## API Methods

The `MultiSheetService` class provides the following methods:

### Insert Operations
```python
def insert_record(sheet_type: SheetType, data: Dict[str, Any]) -> bool
```
- Inserts a new record into the specified sheet
- Validates data against sheet structure
- Auto-generates required fields
- Returns True if successful, False otherwise

### Update Operations
```python
def update_record(sheet_type: SheetType, record_id: str, updates: Dict[str, Any]) -> bool
```
- Updates existing record in the specified sheet
- Only updates provided fields
- Validates update data
- Returns True if successful, False otherwise

### Retrieve Operations
```python
def get_record(sheet_type: SheetType, record_id: str) -> Optional[Dict[str, Any]]
def get_all_records(sheet_type: SheetType, filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]
```
- Retrieves single record or all records
- Supports optional filtering
- Returns structured data as dictionaries

### Delete Operations
```python
def delete_record(sheet_type: SheetType, record_id: str) -> bool
```
- Deletes a record from the specified sheet
- Returns True if successful, False otherwise

## Usage Examples

### Basic Operations

```python
from multi_sheet_service import multi_sheet_service
from sheet_structures import SheetType

# Insert a new pet record
success = multi_sheet_service.insert_record(
    SheetType.PETS,
    {
        "lead_id": "123456789",
        "pet_name": "Max",
        "species": "Dog",
        "breed": "Golden Retriever",
        "weight_kg": 25.5
    }
)

# Update pet information
success = multi_sheet_service.update_record(
    SheetType.PETS,
    "123456789",
    {
        "weight_kg": 26.2,
        "coat_condition": "Excellent"
    }
)

# Get pet record
record = multi_sheet_service.get_record(SheetType.PETS, "123456789")
if record:
    print(f"Pet: {record['pet_name']}, Weight: {record['weight_kg']}kg")
```

### Advanced Operations

```python
# Get all active services
services = multi_sheet_service.get_all_records(
    SheetType.SERVICES,
    filters={"is_active": True}
)

# Get appointments for a specific date
appointments = multi_sheet_service.get_all_records(
    SheetType.APPOINTMENTS,
    filters={"appointment_date": "2024-01-15"}
)

# Bulk insert multiple records
pets_data = [
    {"lead_id": "LEAD001", "pet_name": "Luna", "species": "Cat"},
    {"lead_id": "LEAD002", "pet_name": "Buddy", "species": "Dog"}
]

for pet_data in pets_data:
    multi_sheet_service.insert_record(SheetType.PETS, pet_data)
```

## Data Validation

The system includes comprehensive data validation:

### Required Fields
Each sheet type defines required fields that must be provided for insert operations.

### Data Types
- `string` - Text data
- `number` - Numeric data (automatically converted to float)
- `date` - Date data
- `boolean` - Boolean data (converts strings like "true", "1", "yes" to boolean)

### Auto-Generated Fields
- `pet_id` - Generates "PET" + 6 random characters
- `service_id` - Generates "SVC" + 6 random characters
- `appointment_id` - Generates "APT" + 6 random characters
- `brand_id` - Generates "BRD" + 6 random characters
- `created_date` - Sets current date

### Default Values
Fields can have default values that are automatically applied if not provided.

## Error Handling

The system provides comprehensive error handling:

- **Authentication errors** - Logged and handled gracefully
- **Validation errors** - Detailed error messages for invalid data
- **API errors** - HTTP errors are caught and logged
- **Missing data** - Graceful handling of missing records

## Configuration

### Environment Variables
```bash
DISCORD_BOT_TOKEN=your_discord_bot_token
GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
GOOGLE_SPREADSHEET_ID=your_spreadsheet_id
```

### Google Sheets Setup
1. Create a Google Cloud Project
2. Enable Google Sheets API
3. Create a service account
4. Download credentials.json
5. Share your Google Sheet with the service account email

## Discord Bot Integration

The Discord bot automatically:
1. Creates a pet record when a new thread is created
2. Sets the lead_id to the Discord thread ID
3. Sets status to "initiated"
4. Auto-generates a pet_id

## Best Practices

### 1. Data Consistency
- Always use the same field names as defined in the sheet structures
- Validate data before inserting
- Use appropriate data types

### 2. Error Handling
- Always check return values from service methods
- Handle errors gracefully in your application
- Log errors for debugging

### 3. Performance
- Use filters when retrieving large datasets
- Batch operations when possible
- Cache frequently accessed data

### 4. Security
- Keep credentials secure
- Never commit credentials to version control
- Use environment variables for sensitive data

## Troubleshooting

### Common Issues

1. **"Unknown sheet type" error**
   - Check that you're using the correct SheetType enum value
   - Ensure the sheet structure is defined in sheet_structures.py

2. **"Data validation failed" error**
   - Check required fields are provided
   - Verify data types are correct
   - Review validation error messages

3. **"Record not found" error**
   - Verify the record_id exists
   - Check that you're using the correct sheet type
   - Ensure the record_id format is correct

4. **Authentication errors**
   - Verify credentials.json exists and is valid
   - Check that the service account has access to the sheet
   - Ensure Google Sheets API is enabled

### Debugging

Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Check service status:
```python
if multi_sheet_service.service:
    print("Service is properly configured")
else:
    print("Service is not configured")
```

## Extending the System

### Adding New Sheet Types

1. Add new enum value to `SheetType`
2. Define sheet structure in `SHEET_STRUCTURES`
3. Add field definitions with appropriate validation rules
4. Test with the new sheet type

### Adding New Fields

1. Add field definition to the appropriate sheet structure
2. Update validation rules if needed
3. Test with existing data

### Custom Validation Rules

Add custom validation by extending the `validate_data` function in `sheet_structures.py`.

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review the example files
3. Check the logs for detailed error messages
4. Verify your Google Sheets setup
