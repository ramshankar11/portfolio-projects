# NoBroker Listings Scraper

This is a Python-based automation tool that scrapes NoBroker for new property listings in specific localities and sends notifications via Telegram. It creates a stateful record of seen properties to avoid duplicate alerts.

## Features

- **Web Scraping**: extract property details from NoBroker.
- **State Management**: Tracks seen properties and sent URLs to prevent duplicate notifications (Local or Google Cloud Storage).
- **Notifications**: Sends alerts to a Telegram chat with property details.
- **Cloud Ready**: Can be deployed as a Google Cloud Function or run locally.

## Prerequisite

- Python 3.8+
- A Telegram Bot Token and Chat ID.
- (Optional) Google Cloud Project with Storage enabled for cloud persistence.

## Installation

1.  **Clone the repository** (or navigate to the project folder):
    ```bash
    cd NoBroker_Listings
    ```

2.  **Install dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

## Configuration

The script uses environment variables for configuration. You must set these before running the script.

| Variable | Description | Required |
| :--- | :--- | :--- |
| `TELEGRAM_BOT_TOKEN` | Your Telegram Bot Token. | Yes |
| `TELEGRAM_CHAT_ID` | The Chat ID to receive notifications. | Yes | 
| `GCS_BUCKET_NAME` | Google Cloud Storage bucket name for state. | No (Default: `nobroker`) |

### Setting Environment Variables (Windows PowerShell)

```powershell
$env:TELEGRAM_BOT_TOKEN="your_bot_token_here"
$env:TELEGRAM_CHAT_ID="your_chat_id_here"
```
you can get chatid from https://api.telegram.org/bot{bot_token}/getUpdates -> you can check the chat id in from key in the resulting json
## Usage

### Local Execution

Run the script directly with Python:

```bash
python nobroker_scraper.py
```

The script will:
1.  Load state (seen IDs) from GCS (if available) or start fresh.
2.  Scrape configured NoBroker URLs.
3.  Filter for new properties posted "Today".
4.  Send Telegram notifications for new matches.
5.  Save state back to GCS (if available).

### Cloud Function

The script includes an entry point `nobroker_scraper_gcf_entry` for Google Cloud Functions.
