import os
import logging
import random
import string
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from config import GOOGLE_SHEETS_CREDENTIALS_FILE, SPREADSHEET_ID, WORKSHEET_NAME

logger = logging.getLogger('google_sheets')

class GoogleSheetsService:
    def __init__(self):
        self.credentials = None
        self.service = None
        self.spreadsheet_id = SPREADSHEET_ID
        self.worksheet_name = WORKSHEET_NAME
        
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
    
    def insert_thread_record(self, lead_id):
        """Insert a new thread record into the Google Sheet."""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Skipping thread record insertion.")
            return False
        
        try:
            # Prepare the data row with all columns
            pet_id = "PET" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            row_data = [
                lead_id,        # A: lead_id
                pet_id,         # B: pet_id
                "initiated",    # C: status
                "",            # D: pet_name
                "",            # E: species
                "",            # F: breed
                "",            # G: weight_kg
                "",            # H: age_years
                "",            # I: coat_condition
                ""             # J: notes
            ]
            
            # Define the range (append to the end of the sheet)
            range_name = f"{self.worksheet_name}!A:J"
            
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
            
            logger.info(f"Successfully inserted thread record: {lead_id}")
            logger.debug(f"Updated {result.get('updates').get('updatedCells')} cells")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while inserting thread record: {e}")
            return False
        except Exception as e:
            logger.error(f"Error inserting thread record: {e}")
            return False
    
    def update_thread_record(self, lead_id, **kwargs):
        """
        Update thread record fields. Only lead_id is required, all other fields are optional.
        
        Args:
            lead_id (str): The lead ID to update (required)
            **kwargs: Optional fields to update:
                - pet_name (str): Pet's name
                - species (str): Pet species
                - breed (str): Pet breed
                - weight_kg (float/str): Weight in kg
                - age_years (float/str): Age in years
                - coat_condition (str): Coat condition
                - notes (str): Additional notes
                - status (str): Status of the record
        """
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Skipping record update.")
            return False
        
        if not lead_id:
            logger.error("lead_id is required for updating thread record")
            return False
        
        try:
            # Find the row with the lead_id
            range_name = f"{self.worksheet_name}!A:J"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                logger.warning("No data found in spreadsheet")
                return False
            
            # Find the row with matching lead_id
            row_index = None
            for i, row in enumerate(values):
                if row and str(row[0]) == str(lead_id):
                    row_index = i + 1  # Sheets uses 1-based indexing
                    break
            
            if row_index is None:
                logger.warning(f"Lead ID {lead_id} not found in spreadsheet")
                return False
            
            # Define column mappings (0-based index)
            column_mapping = {
                'pet_name': 'D',      # Column D (index 3)
                'species': 'E',       # Column E (index 4)
                'breed': 'F',         # Column F (index 5)
                'weight_kg': 'G',     # Column G (index 6)
                'age_years': 'H',     # Column H (index 7)
                'coat_condition': 'I', # Column I (index 8)
                'notes': 'J',         # Column J (index 9)
                'status': 'C'         # Column C (index 2)
            }
            
            # Update each provided field
            for field_name, value in kwargs.items():
                if field_name in column_mapping:
                    column_letter = column_mapping[field_name]
                    range_name = f"{self.worksheet_name}!{column_letter}{row_index}"
                    
                    body = {
                        'values': [[str(value)]]
                    }
                    
                    result = self.service.spreadsheets().values().update(
                        spreadsheetId=self.spreadsheet_id,
                        range=range_name,
                        valueInputOption='RAW',
                        body=body
                    ).execute()
                    
                    logger.info(f"Successfully updated {field_name} for lead {lead_id}: {value}")
                else:
                    logger.warning(f"Unknown field '{field_name}' provided for update")
            
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while updating thread record: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating thread record: {e}")
            return False
    
    def get_thread_record(self, lead_id):
        """Get the complete thread record by lead_id."""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Cannot get thread record.")
            return None
        
        try:
            range_name = f"{self.worksheet_name}!A:J"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # Find the row with matching lead_id
            for row in values:
                if row and str(row[0]) == str(lead_id):
                    # Ensure the row has enough columns, pad with empty strings if needed
                    while len(row) < 10:
                        row.append("")
                    
                    return {
                        'lead_id': row[0],
                        'pet_id': row[1],
                        'status': row[2],
                        'pet_name': row[3],
                        'species': row[4],
                        'breed': row[5],
                        'weight_kg': row[6],
                        'age_years': row[7],
                        'coat_condition': row[8],
                        'notes': row[9]
                    }
            
            return None
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while getting thread record: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting thread record: {e}")
            return None

# Create a global instance
sheets_service = GoogleSheetsService()
