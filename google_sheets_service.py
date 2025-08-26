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
        self.spreadsheet_id = "1Mfkt8d5xua0-7zcNF5OpkdSBjputGOxf8D_hL_lLl3M"
        self.worksheet_name = "Sheet1"
        
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
            # Prepare the data row
            pet_id = "PET" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            row_data = [
                lead_id,
                pet_id,
                "initiated",
            ]
            
            # Define the range (append to the end of the sheet)
            range_name = f"{self.worksheet_name}!A:G"
            
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
    
    def update_thread_status(self, lead_id, new_status):
        """Update the status of an existing thread record."""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Skipping status update.")
            return False
        
        try:
            # Find the row with the lead_id
            range_name = f"{self.worksheet_name}!A:F"
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
                logger.warning(f"Thread ID {lead_id} not found in spreadsheet")
                return False
            
            # Update the status column (column F, which is index 5)
            range_name = f"{self.worksheet_name}!F{row_index}"
            body = {
                'values': [[new_status]]
            }
            
            result = self.service.spreadsheets().values().update(
                spreadsheetId=self.spreadsheet_id,
                range=range_name,
                valueInputOption='RAW',
                body=body
            ).execute()
            
            logger.info(f"Successfully updated thread {lead_id} status to: {new_status}")
            return True
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while updating thread status: {e}")
            return False
        except Exception as e:
            logger.error(f"Error updating thread status: {e}")
            return False
    
    def get_thread_status(self, lead_id):
        """Get the current status of a thread."""
        if not self.service or not self.spreadsheet_id:
            logger.warning("Google Sheets service not available. Cannot get thread status.")
            return None
        
        try:
            range_name = f"{self.worksheet_name}!A:F"
            result = self.service.spreadsheets().values().get(
                spreadsheetId=self.spreadsheet_id,
                range=range_name
            ).execute()
            
            values = result.get('values', [])
            if not values:
                return None
            
            # Find the row with matching lead_id
            for row in values:
                if row and str(row[0]) == str(lead_id) and len(row) > 5:
                    return row[5]  # Status is in column F (index 5)
            
            return None
            
        except HttpError as e:
            logger.error(f"HTTP error occurred while getting thread status: {e}")
            return None
        except Exception as e:
            logger.error(f"Error getting thread status: {e}")
            return None

# Create a global instance
sheets_service = GoogleSheetsService()
