import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("DISCORD_BOT_TOKEN environment variable is required")

# Bot settings
BOT_PREFIX = "!"
BOT_DESCRIPTION = "A Discord bot that responds to thread messages related to pet grooming."

# Google Sheets configuration
GOOGLE_SHEETS_CREDENTIALS_FILE = os.getenv('GOOGLE_SHEETS_CREDENTIALS_FILE', 'credentials.json')
SPREADSHEET_ID = os.getenv('GOOGLE_SPREADSHEET_ID')
