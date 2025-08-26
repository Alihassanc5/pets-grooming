#!/usr/bin/env python3
"""
Example usage of the Google Sheets update API for pet grooming records.
This file demonstrates how to update pet information in the Google Sheet.
"""

from google_sheets_service import sheets_service
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def example_updates():
    """Example of how to update pet information in Google Sheets."""
    
    # Example lead_id (this should be a real lead_id from your Discord threads)
    lead_id = "123456789"
    
    print("=== Google Sheets Update Examples ===\n")
    
    # Example 1: Update basic pet information
    print("1. Updating basic pet information...")
    success = sheets_service.update_thread_record(
        lead_id=lead_id,
        pet_name="Max",
        species="Dog",
        breed="Golden Retriever",
        weight_kg=25.5,
        age_years=3
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}\n")
    
    # Example 2: Update coat condition and notes
    print("2. Updating coat condition and notes...")
    success = sheets_service.update_thread_record(
        lead_id=lead_id,
        coat_condition="Good - needs brushing",
        notes="Customer prefers gentle grooming, sensitive to loud noises"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}\n")
    
    # Example 3: Update status
    print("3. Updating status...")
    success = sheets_service.update_thread_record(
        lead_id=lead_id,
        status="in_progress"
    )
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}\n")
    
    # Example 4: Get the complete record
    print("4. Retrieving complete record...")
    record = sheets_service.get_thread_record(lead_id)
    if record:
        print("   Record found:")
        for key, value in record.items():
            print(f"   {key}: {value}")
    else:
        print("   ❌ No record found")
    print()

def update_single_field_example():
    """Example of updating just one field."""
    lead_id = "123456789"
    
    print("=== Single Field Update Example ===")
    print("Updating only the pet name...")
    
    success = sheets_service.update_thread_record(
        lead_id=lead_id,
        pet_name="Buddy"
    )
    
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    print()

def batch_update_example():
    """Example of updating multiple fields at once."""
    lead_id = "123456789"
    
    print("=== Batch Update Example ===")
    print("Updating multiple fields at once...")
    
    success = sheets_service.update_thread_record(
        lead_id=lead_id,
        pet_name="Luna",
        species="Cat",
        breed="Persian",
        weight_kg=4.2,
        age_years=2,
        coat_condition="Matted - needs special attention",
        notes="Long-haired cat, requires daily brushing after grooming",
        status="scheduled"
    )
    
    print(f"Result: {'✅ Success' if success else '❌ Failed'}")
    print()

if __name__ == "__main__":
    print("Google Sheets API Examples for Pet Grooming Bot")
    print("=" * 50)
    
    # Check if the service is properly configured
    if not sheets_service.service:
        print("❌ Google Sheets service is not properly configured.")
        print("Please check your credentials and configuration.")
        exit(1)
    
    # Run examples
    example_updates()
    update_single_field_example()
    batch_update_example()
    
    print("Examples completed!")
