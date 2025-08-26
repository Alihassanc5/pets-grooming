"""
Simple multi-sheet Google Sheets service for handling different types of data.
This service can work with multiple sheets, each with their own structure.
"""

import os
import logging
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from typing import Dict, List, Any, Optional
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, SPREADSHEET_ID
from sheet_structures import SheetType, get_sheet_structure

logger = logging.getLogger('multi_sheet_service')

class GoogleSheetsService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.spreadsheet_id = SPREADSHEET_ID
        
        if not self.spreadsheet_id:
            logger.warning("Google Spreadsheet ID not configured. Google Sheets integration will be disabled.")
            return
            
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Google Sheets API using service account credentials."""
        try:
            # Define the scope
            scope = ['https://www.googleapis.com/auth/spreadsheets']
            
            # Check if credentials file exists
            if not os.path.exists(GOOGLE_SHEETS_CREDENTIALS_FILE):
                logger.error(f"Google Sheets credentials file not found: {GOOGLE_SHEETS_CREDENTIALS_FILE}")
                return
            
            # Load credentials from service account file
            self.credentials = Credentials.from_service_account_file(
                GOOGLE_SHEETS_CREDENTIALS_FILE, 
                scopes=scope
            )
            
            # Build the service
            self.service = build('sheets', 'v4', credentials=self.credentials)
            logger.info("Successfully authenticated with Google Sheets API")
            
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets API: {e}")
            self.service = None
    

    
    def insert_record(self, sheet_type: SheetType, data: Dict[str, Any]) -> bool:
        """
        Insert a new record into the specified sheet type.
        
        Args:
            sheet_type: The type of sheet to insert into
            data: Data to insert
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Skipping record insertion.")
            return False
        
        # Get sheet structure
        structure = get_sheet_structure(sheet_type)
        if not structure:
            logger.error(f"Unknown sheet type: {sheet_type}")
            return False
        
        try:
            # Prepare row data in correct order
            row_data = []
            for field in structure.fields:
                value = data.get(field.name, "")
                row_data.append(str(value) if value is not None else "")
            
            # Define the range (append to the end of the sheet)
            range_name = f"{structure.name}!A:{structure.fields[-1].column}"
            
            # Prepare the request body
            body = {
                'values': [row_data]
            }
            
            # Append the data
            result = self.service.spreadsheets().values().append(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                insertDataOption='INSERT_ROWS',
                body=body
            ).execute()
            
            logger.info(f"Successfully inserted record in {structure.name}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while inserting record: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inserting record: {e}")
            return False
    
    def update_record(self, sheet_type: SheetType, record_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update a record in the specified sheet type.
        
        Args:
            sheet_type: The type of sheet to update
            record_id: The ID of the record to update (usually the first column)
            updates: Fields to update (only provided fields will be updated)
        
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Skipping record update.")
            return False
        
        # Get sheet structure
        structure = get_sheet_structure(sheet_type)
        if not structure:
            logger.error(f"Unknown sheet type: {sheet_type}")
            return False
        
        try:
            # Find the row with the record_id
            range_name = f"{structure.name}!A:{structure.fields[-1].column}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning("No data found in spreadsheet")
                return False
            
            # Find the row with matching record_id
            row_index = None
            for i, row in enumerate(values):
                if row and str(row[0]) == str(record_id):
                    row_index = i + 1  # Sheets uses 1-based indexing
                    break
            
            if row_index is None:
                logger.warning(f"Record ID {record_id} not found in {structure.name}")
                return False
            
            # Update each provided field
            for field_name, value in updates.items():
                # Find the field definition
                field_def = None
                for field in structure.fields:
                    if field.name == field_name:
                        field_def = field
                        break
                
                if field_def:
                    range_name = f"{structure.name}!{field_def.column}{row_index}"
                    body = {
                        'values': [[str(value)]]
                    }
                    
                    result = self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    
                    logger.info(f"Successfully updated {field_name} for {record_id}: {value}")
                else:
                    logger.warning(f"Unknown field '{field_name}' provided for update")
            
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while updating record: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating record: {e}")
            return False
    
    def get_record(self, sheet_type: SheetType, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a record from the specified sheet type.
        
        Args:
            sheet_type: The type of sheet to get from
            record_id: The ID of the record to get (usually the first column)
        
        Returns:
            Dict with record data or None if not found
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Cannot get record.")
            return None
        
        # Get sheet structure
        structure = get_sheet_structure(sheet_type)
        if not structure:
            logger.error(f"Unknown sheet type: {sheet_type}")
            return None
        
        try:
            range_name = f"{structure.name}!A:{structure.fields[-1].column}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # Find the row with matching record_id
            for row in values:
                if row and str(row[0]) == str(record_id):
                    # Ensure the row has enough columns, pad with empty strings if needed
                    while len(row) < len(structure.fields):
                        row.append("")
                    
                    # Convert to dictionary using field names
                    record = {}
                    for i, field in enumerate(structure.fields):
                        if i < len(row):
                            record[field.name] = row[i]
                        else:
                            record[field.name] = ""
                    
                    return record
            
            return None
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while getting record: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting record: {e}")
            return None
    
    def get_all_records(self, sheet_type: SheetType) -> List[Dict[str, Any]]:
        """
        Get all records from the specified sheet type.
        
        Args:
            sheet_type: The type of sheet to get from
        
        Returns:
            List of records as dictionaries
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Cannot get records.")
            return []
        
        # Get sheet structure
        structure = get_sheet_structure(sheet_type)
        if not structure:
            logger.error(f"Unknown sheet type: {sheet_type}")
            return []
        
        try:
            range_name = f"{structure.name}!A:{structure.fields[-1].column}"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return []
            
            records = []
            # Skip the first row (header row) and process all data rows
            for row in values[1:]:
                if not row:
                    continue
                
                # Ensure the row has enough columns, pad with empty strings if needed
                while len(row) < len(structure.fields):
                    row.append("")
                
                # Convert to dictionary using field names
                record = {}
                for i, field in enumerate(structure.fields):
                    if i < len(row):
                        record[field.name] = row[i]
                    else:
                        record[field.name] = ""
                
                records.append(record)
            
            logger.info(f"Successfully retrieved {len(records)} records from {structure.name}")
            return records
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while getting records: {e}")
            return []
        except Exception as e:
            logger.error(f"Error getting records: {e}")
            return []

# Create a global instance
goole_sheet_service = GoogleSheetsService()
