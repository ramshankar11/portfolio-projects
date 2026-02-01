import os
import re
import time
import html
import pickle
import logging
from datetime import datetime, date
from typing import List, Set, Optional, Dict, Any, Tuple

import requests
from bs4 import BeautifulSoup

# Try importing functions_framework for Cloud Functions
# If not present (local run), we skip it gracefully
try:
    import functions_framework
except ImportError:
    functions_framework = None

# --- Configuration Constants ---
# Hardcoded defaults REMOVED for security.
# Configuration must be provided via Environment Variables.
DEFAULT_GCS_BUCKET_NAME = "nobroker"

TARGET_URLS = [
    # eg: you can get this link after you have selected your reuired filters in the ui AND you can copy that linkk after putting all your filters
    "https://www.nobroker.in/property/rent/chennai/multiple?searchParam=W3sibGF0IjoxMy4wMjEyODA1LCJsb24iOjgwLjIyMzEwMzcsInBsYWNlSWQiOiJDaElKaTBRTW9ScG5Vam9SQXhnNTRvMnRMUFkiLCJwbGFjZU5hbWUiOiJTYWlkYXBldCIsInNob3dNYXAiOmZhbHNlfSx7ImxhdCI6MTMuMDA2NjYyNSwibG9uIjo4MC4yMjA2MzY5LCJwbGFjZUlkIjoiQ2hJSmZRcWttbkJuVWpvUlVDZFJfSldHTk1vIiwicGxhY2VOYW1lIjoiR3VpbmR5Iiwic2hvd01hcCI6ZmFsc2V9LHsibGF0IjoxMy4wNDE3NTkxLCJsb24iOjgwLjIzNDA3NjEsInBsYWNlSWQiOiJDaElKY1NQYXBWVm1Vam9SOEVyd1E1ZjBWRWsiLCJwbGFjZU5hbWUiOiJULiBOYWdhciIsInNob3dNYXAiOmZhbHNlfV0=&radius=2.0&sharedAccomodation=0&city=chennai&locality=Saidapet,Guindy,T.%20Nagar&isMetro=false&orderBy=lastUpdateDate,desc&rent=0,11000",
    "https://www.nobroker.in/property/rent/chennai/multiple?searchParam=W3sibGF0IjoxMi45MzQ4OTEyLCJsb24iOjgwLjIxMzcxMjM5OTk5OTk5LCJwbGFjZUlkIjoiQ2hJSjJmOFVfVXhjVWpvUkMyRG9LQWNGVFRzIiwicGxhY2VOYW1lIjoiUGFsbGlrYXJhbmFpIiwic2hvd01hcCI6ZmFsc2V9LHsibGF0IjoxMi45NjQ3NDYyLCJsb24iOjgwLjE5NjA4MzE5OTk5OTk5LCJwbGFjZUlkIjoiQ2hJSndiMDZSdWxkVWpvUlBaYUNXQWVDSHdjIiwicGxhY2VOYW1lIjoiTWFkaXBha2thbSIsInNob3dNYXAiOmZhbHNlfSx7ImxhdCI6MTIuOTQwODY1LCJsb24iOjgwLjE4NTA1OTYsInBsYWNlSWQiOiJDaElKYjlkUFFjMWRVam9SXzdKZEVqZUhfTG8iLCJwbGFjZU5hbWUiOiJLb3ZpbGFtYmFra2FtIiwic2hvd01hcCI6ZmFsc2V9XQ==&radius=2.0&sharedAccomodation=0&city=chennai&locality=Pallikaranai,Madipakkam,Kovilambakkam&isMetro=false&orderBy=lastUpdateDate,desc&rent=0,11000",
]

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
}

SEEN_IDS_BLOB_NAME = 'nobroker_seen_property_ids.pkl'
SENT_URLS_BLOB_NAME = 'nobroker_sent_property_urls.pkl'

# Try importing Google Cloud Storage
# If not present (local run without SDK), we handle gracefully
try:
    from google.cloud import storage
    GCS_AVAILABLE = True
except ImportError:
    GCS_AVAILABLE = False
    print("WARNING: google-cloud-storage not installed. Persistence will be disabled (Local Mode).")


class NoBrokerScraper:
    def __init__(self):
        # API Configuration
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
        self.gcs_bucket_name = os.environ.get('GCS_BUCKET_NAME', DEFAULT_GCS_BUCKET_NAME)

        if not self.telegram_token or not self.telegram_chat_id:
            print("WARNING: Telegram Token or Chat ID not found in environment variables. DMs will not be sent.")
        
        # Runtime State
        self.session = requests.Session()
        self.session.headers.update(HEADERS)
        self.seen_ids: Set[str] = set()
        self.sent_urls: Set[str] = set()
        
        # GCS Clients
        self.storage_client = None
        self.bucket = None
        self.seen_blob = None
        self.sent_blob = None

    def _initialize_gcs(self):
        """Initialize Google Cloud Storage clients."""
        if not GCS_AVAILABLE:
            return

        try:
            if not self.storage_client:
                self.storage_client = storage.Client()
                self.bucket = self.storage_client.bucket(self.gcs_bucket_name)
                self.seen_blob = self.bucket.blob(SEEN_IDS_BLOB_NAME)
                self.sent_blob = self.bucket.blob(SENT_URLS_BLOB_NAME)
                print(f"GCS clients initialized for bucket: {self.gcs_bucket_name}")
        except Exception as e:
            print(f"CRITICAL: Failed to initialize GCS clients: {e}")

    def _load_state(self):
        """Load seen IDs and sent URLs from GCS."""
        self._initialize_gcs()
        
        # Load Seen IDs
        if self.seen_blob and self.seen_blob.exists():
            try:
                data = self.seen_blob.download_as_string()
                self.seen_ids = pickle.loads(data)
                print(f"Loaded {len(self.seen_ids)} seen property IDs from GCS.")
            except Exception as e:
                print(f"Error loading seen IDs: {e}. Starting fresh.")
                self.seen_ids = set()
        else:
            print("No existing seen IDs blob found. Starting fresh.")

        # Load Sent URLs
        if self.sent_blob and self.sent_blob.exists():
            try:
                data = self.sent_blob.download_as_string()
                self.sent_urls = pickle.loads(data)
                print(f"Loaded {len(self.sent_urls)} sent property URLs from GCS.")
            except Exception as e:
                print(f"Error loading sent URLs: {e}. Starting fresh.")
                self.sent_urls = set()
        else:
            print("No existing sent URLs blob found. Starting fresh.")

    def _save_state(self):
        """Save current state to GCS."""
        if not self.bucket:
            print("GCS bucket not connected. Skipping save.")
            return

        try:
            if self.seen_blob:
                self.seen_blob.upload_from_string(pickle.dumps(self.seen_ids))
                print(f"Saved {len(self.seen_ids)} seen IDs to GCS.")
        except Exception as e:
            print(f"Error saving seen IDs: {e}")

        try:
            if self.sent_blob:
                self.sent_blob.upload_from_string(pickle.dumps(self.sent_urls))
                print(f"Saved {len(self.sent_urls)} sent URLs to GCS.")
        except Exception as e:
            print(f"Error saving sent URLs: {e}")

    def _send_telegram_notification(self, message_html: str):
        """Send a notification to Telegram."""
        if not self.telegram_token or not self.telegram_chat_id:
            print("CRITICAL: Telegram credentials missing. Notification not sent.")
            return

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {
            'chat_id': self.telegram_chat_id,
            'text': message_html,
            'parse_mode': 'HTML'
        }
        
        try:
            response = self.session.post(url, data=payload, timeout=10)
            response.raise_for_status()
            print(f"    Telegram notification sent to chat ID {self.telegram_chat_id}!")
        except requests.exceptions.RequestException as e:
            print(f"    Failed to send Telegram notification: {e}")

    @staticmethod
    def _clean_text(text: Optional[str]) -> str:
        if not text:
            return "N/A"
        text = re.sub(r'<!--.*?-->', '', str(text))
        text = text.replace('₹', '').replace(',', '').strip()
        if '+' in text:
            text = text.split('+')[0].strip()
        # Strictly keep only digits and dots (matches reference script)
        cleaned_text = re.sub(r'[^\d.]', '', text)
        return cleaned_text

    @staticmethod
    def _parse_date(date_str: Optional[str]) -> Any:
        if not date_str:
            return None
        date_str_lower = date_str.lower()
        if "ready to move" in date_str_lower:
            return "Ready to Move"
        if "today" in date_str_lower:
            return datetime.now().date()
        
        clean_str = re.sub(r'<!--.*?-->', '', date_str).strip()
        # FIX: Added '%b%d,%Y' to handle cases like 'Jan31,2026'
        formats = ['%b %d, %Y', '%Y-%m-%d', '%d-%b-%Y', '%d-%m-%Y', '%b%d,%Y', '%b %d,%Y']
        
        for fmt in formats:
            try:
                return datetime.strptime(clean_str, fmt).date()
            except ValueError:
                continue
        return None

    def _fetch_page_content(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch a URL and return a BeautifulSoup object."""
        try:
            # Shorten URL for cleaner logs
            log_url = url.split('?')[0]
            # print(f"    Fetching: {log_url}...") 
            time.sleep(0.5)
            response = self.session.get(url, timeout=20)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def _extract_detail_text(self, soup: BeautifulSoup, tag_name: str, **kwargs) -> str:
        tag = soup.find(tag_name, **kwargs)
        if tag:
            return re.sub(r'<!--.*?-->', '', tag.get_text(strip=True)).strip()
        return "N/A"

    def _get_detailed_info(self, url: str) -> Dict[str, str]:
        """Fetch the detailed property page to get extended info."""
        details = {}
        print(f"    Fetching details for: {url}")
        soup = self._fetch_page_content(url)
        if not soup:
            return details

        # Summary Section
        summary_container = soup.find('section', id='property-summary-container')
        if summary_container:
            details['bedrooms'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-typeDesc')
            details['property_type'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-buildingType')
            details['preferred_tenant'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-leaseType')
            details['parking'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-parkingDesc')
            details['age'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-propertyAge')
            details['posted_on'] = self._extract_detail_text(summary_container, 'h4', id='details-summary-lastUpdateDate')
            
        # Overview Section
        overview_section = soup.find('div', class_='nb__33JWL')
        if overview_section:
            def get_overview_item(label: str):
                title_tag = overview_section.find('h5', id='overviewTitle', string=re.compile(re.escape(label), re.IGNORECASE))
                if title_tag:
                    val_div = title_tag.find_parent(class_="nb__2vvM7").find_next_sibling(class_="nb__2xbus")
                    if val_div:
                         return val_div.get_text(strip=True)
                return "N/A"

            details['furnishing'] = get_overview_item('Furnishing Status')
            details['floor'] = get_overview_item('Floor')
            details['bathroom'] = get_overview_item('Bathroom')
            details['balconies'] = get_overview_item('Balcony')
            
        return details

    def _parse_card(self, card: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """Parse a single property card from the listing page."""
        try:
            main_div = card.find('div', class_=lambda x: x and 'nb__2_XSE' in x.split())
            if not main_div or not main_div.get('id'):
                return None
            
            prop_id = main_div['id']
            
            url = None
            title_h2 = main_div.find('h2', class_='heading-6')
            if title_h2:
                a_tag = title_h2.find('a', href=True)
                if a_tag:
                    url = "https://www.nobroker.in" + a_tag['href']
            
            # URL Fallback (from reference script)
            if not url:
                section_tag = main_div.find('section')
                if section_tag:
                    link_tag_fallback = section_tag.find('a', href=True)
                    if link_tag_fallback:
                        url = "https://www.nobroker.in" + link_tag_fallback['href']

            if not url:
                return None

            data = {'id': prop_id, 'url': url}

            # Price
            price_span = main_div.find('span', itemprop='price')
            if price_span:
                data['price'] = self._clean_text(price_span.get_text())
            else:
                rent_div = main_div.find('div', id='minimumRent')
                if rent_div:
                   data['price'] = self._clean_text(rent_div.get_text())
                   # FIX: Explicit "Lease Only" Logic matching reference script
                   if rent_div and "only deposit" in rent_div.get_text(strip=True).lower():
                       data['price'] = "Lease Only"
            
            if not data.get('price'): 
                data['price'] = "N/A"

            # Deposit
            deposit_head = main_div.find(lambda t: t.name == 'div' and 'Deposit' in t.text and 'heading-7' in t.get('class', []))
            if deposit_head:
                deposit_val = deposit_head.find_previous_sibling('div')
                data['deposit'] = self._clean_text(deposit_val.get_text()) if deposit_val else "N/A"
            else:
                data['deposit'] = "N/A"

            # Date fallback
            event_span = main_div.find('span', itemprop='event')
            if event_span:
                start_date = event_span.find('span', itemprop='startDate')
                if start_date:
                    data['posted_on_card'] = start_date.get_text(strip=True)
            
            # FIX: Additional Fallback: Available From (matching reference script)
            if not data.get('posted_on_card'):
                available_from_head = main_div.find(lambda t: t.name == 'div' and "Available From" in t.get_text() and "heading-7" in t.get('class', []))
                if available_from_head:
                    date_val_div = available_from_head.find_previous_sibling('div', class_='font-semibold')
                    if date_val_div:
                        data['posted_on_card'] = date_val_div.get_text(strip=True)

            return data

        except Exception as e:
            print(f"Error parsing card {card.get('id', 'unknown')}: {e}")
            return None

    def process_property(self, prop_data: Dict[str, Any], today: date) -> bool:
        """
        Process a property: fetch details, check date, notify if new.
        Returns True if a notification was sent.
        """
        prop_id = prop_data['id']
        prop_url = prop_data['url']

        is_new_id = prop_id not in self.seen_ids
        is_unsent_url = prop_url not in self.sent_urls

        if not is_new_id and not is_unsent_url:
            print(f"    [Skipping] ID: {prop_id} (Already Seen/Sent)")
            return False

        # Fetch full details
        details = self._get_detailed_info(prop_url)
        prop_data.update(details)

        # Date Logic
        date_str = prop_data.get('posted_on') or prop_data.get('posted_on_card')
        parsed_date = self._parse_date(date_str)
        
        is_today = False
        if parsed_date == "Ready to Move":
            if is_new_id: 
                is_today = True
        elif isinstance(parsed_date, date):
            if parsed_date == today:
                is_today = True
        
        # Debug Log Inserted Here
        print(f"    [Checking] ID: {prop_id} | Date: '{date_str}' ({parsed_date}) | Today: {today}")

        # Notification Logic
        if is_today and is_unsent_url:
            self._notify(prop_data)
            self.seen_ids.add(prop_id)
            self.sent_urls.add(prop_url)
            return True
        
        if not is_today:
             print(f"    [Skipping] ID: {prop_id} (Old Date: {parsed_date})")

        if is_new_id:
            self.seen_ids.add(prop_id)
        
        return False

    def _notify(self, data: Dict[str, Any]):
        """Constructs and sends the formatted Telegram message."""
        price = data.get('price', 'N/A')
        deposit = data.get('deposit', 'N/A')
        
        price_disp = f"₹{price}" if price != "N/A" and price != "Lease Only" else price
        dep_disp = f"₹{deposit}" if deposit != "N/A" else "N/A"

        lines = [
            "<b>🏡✨ NEW PROPERTY FOUND! ✨</b>",
            f"<b>Posted On:</b> {html.escape(str(data.get('posted_on', 'N/A')))}",
            f"<b>Price:</b> {html.escape(price_disp)}",
            f"<b>Deposit:</b> {html.escape(dep_disp)}",
            f"<b>Type:</b> {html.escape(data.get('bedrooms', 'N/A'))} ({html.escape(data.get('property_type', 'N/A'))})",
            f"<b>Furnishing:</b> {html.escape(data.get('furnishing', 'N/A'))}",
            f"<b>Floor:</b> {html.escape(data.get('floor', 'N/A'))}",
            f"<b>Bathrooms:</b> {html.escape(data.get('bathroom', 'N/A'))}",
            f"<b>Parking:</b> {html.escape(data.get('parking', 'N/A'))}",
            f"<b>URL:</b> <a href=\"{html.escape(data['url'])}\">View Property</a>"
        ]
        
        message = "\n".join(lines)
        
        # Safe ASCII print for Windows consoles
        print(f"\n+++ NEW PROPERTY FOUND & NOT SENT BEFORE! +++") 
        print(f"  ID: {data['id']}, URL: {data['url']}")
        
        # Replace Rupee symbol with 'Rs.' for console log only to avoid UnicodeEncodeError
        console_price = str(price_disp).replace("₹", "Rs. ")
        print(f"  Details: Posted: {data.get('posted_on', 'N/A')}, Price: {console_price}")
        
        self._send_telegram_notification(message)

    def run_cycle(self):
        """Main execution cycle."""
        print("\n--- Starting Execution Cycle ---")
        self._load_state()
        
        today = datetime.now().date()
        print(f"Checking for properties posted on: {today}")

        notifications_sent = 0

        for url in TARGET_URLS:
            print(f"\nScanning URL: {url.split('?')[0]}...")
            soup = self._fetch_page_content(url)
            if not soup:
                continue

            articles = soup.find_all('article')
            count = 0
            found_count = len([a for a in articles if a.find('div', class_=lambda x: x and 'nb__2_XSE' in x.split())])
            print(f"Found {found_count} cards on page. Processing up to 15...")

            for article in articles:
                if count >= 15: 
                    break
                
                card_data = self._parse_card(article)
                if card_data:
                    if self.process_property(card_data, today):
                        notifications_sent += 1
                    count += 1
            
        print(f"\nCycle complete. Notifications sent this run: {notifications_sent}")
        self._save_state()
        print("--- Execution End ---\n")


# --- Cloud Function Entry Point ---
if functions_framework:
    @functions_framework.http
    def nobroker_scraper_gcf_entry(request):
        """
        Entry point for Google Cloud Function.
        """
        try:
            scraper = NoBrokerScraper()
            scraper.run_cycle()
            return ("Execution Successful", 200)
        except Exception as e:
            print(f"Fatal Error in GCF execution: {e}")
            return (f"Execution Failed: {e}", 500)
else:
    # Dummy placeholder if locally testing without functions_framework
    def nobroker_scraper_gcf_entry(request):
        print("Function framework not available, running locally.")
        scraper = NoBrokerScraper()
        scraper.run_cycle()
        return ("Local Run Complete", 200)

# --- Local Execution Entry Point ---
if __name__ == "__main__":
    print("Running in Local / Standalone Mode")
    scraper = NoBrokerScraper()
    scraper.run_cycle()