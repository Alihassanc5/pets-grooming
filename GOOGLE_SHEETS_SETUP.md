# Google Sheets Integration Setup Guide

This guide will help you set up Google Sheets integration for the Discord bot to track thread creation.

## Prerequisites

- A Google account
- A Google Cloud Project
- A Google Sheet with the following columns:
  - A: lead_id
  - B: pet_id
  - C: status
  - D: pet_name
  - E: species
  - F: breed
  - G: weight_kg
  - H: age_years
  - I: coat_condition
  - J: notes

## Step 1: Create a Google Cloud Project

1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the Google Sheets API:
   - Go to "APIs & Services" > "Library"
   - Search for "Google Sheets API"
   - Click on it and press "Enable"

## Step 2: Create a Service Account

1. In your Google Cloud Project, go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "Service Account"
3. Fill in the service account details:
   - Name: `discord-bot-sheets`
   - Description: `Service account for Discord bot Google Sheets integration`
4. Click "Create and Continue"
5. Skip the optional steps and click "Done"

## Step 3: Generate Service Account Key

1. In the Credentials page, find your service account and click on it
2. Go to the "Keys" tab
3. Click "Add Key" > "Create new key"
4. Choose "JSON" format
5. Click "Create" - this will download a JSON file
6. Rename the downloaded file to `credentials.json` and place it in your project root

## Step 4: Set Up Google Sheet

1. Create a new Google Sheet or use an existing one
2. Set up the following columns in the first row:
   ```
   A1: lead_id
   B1: pet_id
   C1: status
   D1: pet_name
   E1: species
   F1: breed
   G1: weight_kg
   H1: age_years
   I1: coat_condition
   J1: notes
   ```
3. Copy the Spreadsheet ID from the URL:
   - The URL looks like: `https://docs.google.com/spreadsheets/d/SPREADSHEET_ID/edit`
   - Copy the part between `/d/` and `/edit`

## Step 5: Share the Sheet with Service Account

1. In your Google Sheet, click "Share" (top right)
2. Add the service account email (found in your `credentials.json` file under `client_email`)
3. Give it "Editor" permissions
4. Click "Send" (you can uncheck "Notify people")

## Step 6: Configure Environment Variables

1. Copy `env_example.txt` to `.env`:
   ```bash
   cp env_example.txt .env
   ```

2. Edit `.env` and add your configuration:
   ```
   DISCORD_BOT_TOKEN=your_discord_bot_token
   GOOGLE_SHEETS_CREDENTIALS_FILE=credentials.json
   GOOGLE_SPREADSHEET_ID=your_spreadsheet_id_here
   GOOGLE_WORKSHEET_NAME=Threads
   ```

## Step 7: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 8: Test the Integration

1. Run the bot:
   ```bash
   python discord_bot.py
   ```

2. Create a new thread in Discord
3. Check your Google Sheet - you should see a new row with:
   - lead_id (Discord thread ID)
   - pet_id (auto-generated PET code)
   - status: "initiated"
   - pet_name (empty)
   - species (empty)
   - breed (empty)
   - weight_kg (empty)
   - age_years (empty)
   - coat_condition (empty)
   - notes (empty)

## Troubleshooting

### Common Issues

1. **"Service account credentials not found"**
   - Make sure `credentials.json` is in the project root
   - Check that the file path in `.env` is correct

2. **"Spreadsheet not found"**
   - Verify the Spreadsheet ID is correct
   - Make sure the service account has access to the sheet

3. **"Permission denied"**
   - Ensure the service account email has "Editor" permissions on the sheet
   - Check that the Google Sheets API is enabled

4. **"Invalid credentials"**
   - Regenerate the service account key
   - Make sure the JSON file is not corrupted

### Security Notes

- Never commit `credentials.json` to version control
- Keep your service account credentials secure
- Consider using environment variables for sensitive data in production

## API Methods Available

The `GoogleSheetsService` class provides these methods:

- `insert_thread_record(lead_id)` - Add a new thread record
- `update_thread_record(lead_id, **kwargs)` - Update any field(s) in a thread record
- `get_thread_record(lead_id)` - Get complete thread record

## Example Usage

```python
# Insert a new thread record (automatically done when thread is created)
sheets_service.insert_thread_record(lead_id="123456789")

# Update pet information
sheets_service.update_thread_record(
    lead_id="123456789",
    pet_name="Max",
    species="Dog",
    breed="Golden Retriever",
    weight_kg=25.5,
    age_years=3,
    coat_condition="Good - needs brushing",
    notes="Customer prefers gentle grooming"
)

# Update just one field
sheets_service.update_thread_record(
    lead_id="123456789",
    status="completed"
)

# Get complete thread record
record = sheets_service.get_thread_record("123456789")
print(f"Pet name: {record['pet_name']}")
print(f"Status: {record['status']}")
```

## Discord Bot Commands

The bot also provides Discord commands for updating records:

- `!update <lead_id> pet_name:Max species:Dog breed:Golden Retriever` - Update multiple fields
- `!get <lead_id>` - Get complete pet information
