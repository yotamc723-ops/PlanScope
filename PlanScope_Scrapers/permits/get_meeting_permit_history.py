"""
Committee Decisions Scraper - Proxy Support Edition

This script reads permit IDs from 'permit_numbers.txt', fetches the data from the Bat Yam API,
and systematically extracts "Committee Meetings and Decisions".

Key Features:
1. Proxy Support: Routes traffic through your paid proxy to avoid IP bans.
2. Stealthy Timing: Random delays between requests.
3. Captcha/Block Detection: Pauses if 403/429 errors or 'captcha' text is detected.
4. Resilience: Retries failed requests.
5. Output: Saves a flat JSON list of all meetings found.

Usage:
    1. Ensure 'permit_numbers.txt' exists.
    2. Create a .env file in the project root with PROXY_USER and PROXY_PASS.
    3. pip install requests beautifulsoup4 python-dotenv
    4. python scraper_proxy.py
"""

import os
import json
import time
import random
import string
import re
import logging
from typing import Any, Dict, List, Optional, Tuple
from requests.exceptions import RequestException, HTTPError
import requests
from bs4 import BeautifulSoup
import urllib3
from dotenv import load_dotenv

# Suppress SSL warnings since verify=False is often needed for proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# PROXY CONFIGURATION (Environment Variables)
# ============================================================================
USE_PROXY = True  # שנה ל-False אם אתה רוצה לעבוד בלי פרוקסי

# טעינת משתני סביבה מקובץ .env או .env.example שנמצא שתי תיקיות למעלה (שורש הפרויקט)
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
env_path = os.path.join(base_path, '.env')
env_example_path = os.path.join(base_path, '.env.example')

# Try .env first, then fallback to .env.example
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    env_file_used = env_path
elif os.path.exists(env_example_path):
    load_dotenv(dotenv_path=env_example_path)
    env_file_used = env_example_path
else:
    env_file_used = None

# פרטי הפרוקסי (קבל אותם מהדשבורד של Bright Data / הספק שלך)
# UPDATED: Changed default to zproxy.lum-superproxy.io which often works better for specific targets
PROXY_HOST = os.getenv("PROXY_HOST", "zproxy.lum-superproxy.io")
PROXY_PORT = os.getenv("PROXY_PORT", "22225")  # Default Bright Data residential port

# טעינת שם המשתמש והסיסמה משתני הסביבה
# For Bright Data, username format is usually: brd-customer-{customer_id}-zone-{zone_name}
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

if USE_PROXY and (not PROXY_USER or not PROXY_PASS):
    if env_file_used:
        print(f"⚠️ WARNING: PROXY_USER or PROXY_PASS not found in env file (looked at: {env_file_used})")
    else:
        print(f"⚠️ WARNING: PROXY_USER or PROXY_PASS not found. No .env or .env.example file found at: {base_path}")

# ============================================================================
# CONFIGURATION
# ============================================================================

API_URL_TEMPLATE = (
    "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
    "?appname=cixpa&prgname=GetBakashaFile&siteid=81&b={permit_id}&arguments=siteid,b"
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Referer': 'https://batyam.complot.co.il/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1'
}

# --- RATE LIMITING & ANTI-BOT (OPTIMIZED FOR PROXY) ---
# עדכון: הורדנו זמנים כי יש פרוקסי שמגן עלינו
REQUEST_DELAY_MIN = 1.0      # מינימום שנייה (היה 2.0)
REQUEST_DELAY_MAX = 3.5      # מקסימום 3.5 שניות (היה 6.0)

BATCH_SIZE_MIN = 50          # הפסקה גדולה כל 50 בקשות
BATCH_SIZE_MAX = 100
LONG_PAUSE_MIN = 5.0         # הפסקה קצרה יותר לקפה (היה 10)
LONG_PAUSE_MAX = 15.0

# Captcha Handling
CAPTCHA_PAUSE_SECONDS = 60   # פחות זמן המתנה כי אפשר אולי להחליף IP (תלוי בסוג הפרוקסי)
MAX_RETRIES = 3              
REQUEST_TIMEOUT = 45         # פרוקסי לפעמים איטי יותר, נתנו לו עוד זמן

# SSL Verification (set to False if proxy causes SSL errors)
# CRITICAL FIX: Defaulting to False for proxies to avoid handshake errors which cause 502s
VERIFY_SSL = os.getenv("VERIFY_SSL", "False").lower() == "true"

# Files
PERMIT_FILE = "opportunities.json"  # Changed from permit_numbers.txt to opportunities.json
OUTPUT_FILE = "committee_decisions.json"
ERROR_LOG_FILE = "errors.log"

# ============================================================================
# LOGGING SETUP
# ============================================================================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_proxy_dict(session_id=None):
    """
    Builds the proxy dictionary for requests.
    If session_id is provided, it appends it to the username to force IP rotation (Bright Data specific).
    Also forces country-il targeting.
    """
    if not USE_PROXY:
        return None
    
    current_user = PROXY_USER
    
    # Bright Data Logic
    if current_user and 'brd-customer' in current_user:
        # Force Israel targeting if not already in username
        if '-country-' not in current_user:
             current_user = f"{current_user}-country-il"
        
        # IP Rotation Logic
        if session_id:
            # Append session ID to username: user-session-ID
            current_user = f"{current_user}-session-{session_id}"

    # Construct the URL with authentication
    if current_user and PROXY_PASS:
        proxy_url_http = f"http://{current_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
        proxy_url_https = f"https://{current_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    else:
        # Fallback if env vars are missing
        proxy_url_http = f"http://{PROXY_HOST}:{PROXY_PORT}"
        proxy_url_https = f"https://{PROXY_HOST}:{PROXY_PORT}"
    
    return {
        "http": proxy_url_http,
        "https": proxy_url_https,
    }

def test_proxy_connection():
    """Test if proxy is working."""
    if not USE_PROXY:
        return True
    
    # Use a random session for the test to ensure we get a fresh IP
    rand_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=rand_session)
    
    print(f"   Using Proxy Host: {PROXY_HOST}")
    print(f"   SSL Verification: {VERIFY_SSL}")
    
    try:
        # Test with a simple request
        print("   Connecting to httpbin.org/ip...")
        test_response = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=15,
            verify=VERIFY_SSL
        )
        if test_response.status_code == 200:
            ip_info = test_response.json()
            origin_ip = ip_info.get('origin')
            print(f"✅ Proxy test successful! Your external IP is: {origin_ip}")
            # Optional: Warning if IP looks non-Israeli (rough check, can't be precise here)
            return True
        else:
            print(f"⚠️  Proxy test returned status {test_response.status_code}")
            return False

    except requests.exceptions.ProxyError as e:
        error_str = str(e)
        if "Failed to resolve" in error_str or "nodename nor servname" in error_str:
            print(f"⚠️  Proxy test failed: Cannot resolve proxy hostname '{PROXY_HOST}'")
            print(f"   💡 Tip: For Bright Data, use PROXY_HOST=zproxy.lum-superproxy.io")
        else:
            print(f"⚠️  Proxy test failed (ProxyError): {e}")
        return False
    except requests.exceptions.SSLError as e:
        print(f"⚠️  Proxy test failed (SSLError): {e}")
        print(f"   💡 Tip: Make sure VERIFY_SSL is False")
        return False
    except Exception as e:
        print(f"⚠️  Proxy test failed (General Error): {e}")
        return False
    return False

def _get_text(el) -> Optional[str]:
    if not el:
        return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def _has_meetings(soup: BeautifulSoup) -> bool:
    """Check if permit has meetings by looking for span.spn in btn-meetings."""
    btn_meetings = soup.find('div', id='btn-meetings')
    if not btn_meetings:
        return False
    
    count_span = btn_meetings.find('span', class_='spn')
    if count_span:
        count_text = count_span.get_text(strip=True)
        match = re.search(r'\((\d+)\)', count_text)
        if match:
            count = int(match.group(1))
            return count > 0
    return False

def _parse_meetings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    """Parse meetings table structure robustly."""
    meetings = []
    
    table_div = soup.find('div', id='table-meetings')
    if not table_div:
        return []
        
    main_table = table_div.find('table')
    if not main_table:
        return []
        
    tbody = main_table.find('tbody')
    if not tbody:
        return []

    all_rows = tbody.find_all('tr', recursive=False)
    i = 0
    
    while i < len(all_rows):
        row = all_rows[i]
        classes = row.get('class', [])
        
        # Look for accordion-toggle row (meeting header row)
        if 'accordion-toggle' in classes:
            cols = row.find_all('td', recursive=False)
            meeting_id = None
            meeting_date = None
            meeting_url = None
            
            # Method 1: Find meeting_id from link
            meeting_link = row.find('a', href=lambda x: x and 'getMeeting' in str(x))
            
            if meeting_link:
                meeting_id = _get_text(meeting_link)
                onclick = meeting_link.get('href', '')
                match = re.search(r'getMeeting\((\d+),(\d+)\)', onclick)
                if match:
                    meeting_type = match.group(1)
                    meeting_num = match.group(2)
                    meeting_url = f"https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetVaadaFile&siteid=81&t={meeting_type}&v={meeting_num}&arguments=siteid,t,v"
            
            # Method 2: Fallback - find meeting number in tds
            if not meeting_id:
                for col in cols:
                    text = _get_text(col)
                    if text and re.match(r'^\d{8,}$', text.strip()):
                        meeting_id = text.strip()
                        break
            
            # Find meeting_date
            for col in cols:
                text = _get_text(col)
                if text and re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
                    meeting_date = text.strip()
                    break
            
            # Now look for the corresponding hiddenRow with details
            essence = None
            decision_status = None
            
            j = i + 1
            while j < len(all_rows):
                next_row = all_rows[j]
                next_classes = next_row.get('class', [])
                
                if 'accordion-toggle' in next_classes:
                    break
                
                hidden_td = next_row.find('td', class_='hiddenRow')
                if hidden_td or 'hiddenRow' in next_classes:
                    details_div = (
                        next_row.find('div', class_=lambda x: x and 'accordian-body' in str(x).lower()) or
                        next_row.find('div', class_=lambda x: x and 'accordion-body' in str(x).lower()) or
                        next_row.find('div', id=lambda x: x and str(meeting_id) in str(x))
                    )
                    
                    if details_div:
                        section_tables = details_div.find_all('table')
                        for table in section_tables:
                            thead = table.find('thead')
                            if not thead: continue
                            th = thead.find('th')
                            if not th: continue
                            th_text = _get_text(th)
                            if not th_text: continue
                            
                            table_tbody = table.find('tbody')
                            if not table_tbody: continue
                            content_td = table_tbody.find('td')
                            if not content_td: continue
                            content = _get_text(content_td)
                            
                            if 'מהות' in th_text:
                                essence = content
                            elif 'החלטות' in th_text:
                                decision_status = content
                    break
                j += 1

            if meeting_id:
                meetings.append({
                    'meeting_id': meeting_id,
                    'meeting_date': meeting_date,
                    'meeting_url': meeting_url,
                    'essence': essence,
                    'decision_status': decision_status
                })
        i += 1
        
    return meetings

def detect_captcha_blocking(response: requests.Response) -> Tuple[bool, str]:
    """Professional captcha/blocking detection."""
    # 502 handled in fetch loop
    
    if response.status_code == 403:
        return True, f"HTTP 403 Forbidden - Request blocked"
    if response.status_code == 429:
        return True, f"HTTP 429 Too Many Requests - Rate limited"
    if response.status_code == 503:
        return True, f"HTTP 503 Service Unavailable - Server blocking"
    
    # Only check for small responses if status is not 502 (502 often has 0 bytes)
    if response.status_code != 502 and len(response.content) < 500:
        return True, f"Suspiciously small response ({len(response.content)} bytes) - likely block page"

    if 'Retry-After' in response.headers:
        retry_after = response.headers['Retry-After']
        return True, f"Rate limit header detected - Retry-After: {retry_after} seconds"

    content_lower = response.text.lower()
    captcha_keywords = {
        'captcha': 'CAPTCHA challenge detected',
        'recaptcha': 'reCAPTCHA detected',
        'access denied': 'Access denied',
        'blocked': 'Blocked',
        'forbidden': 'Forbidden',
        'cloudflare': 'Cloudflare protection',
        'security check': 'Security check'
    }
    
    for keyword, description in captcha_keywords.items():
        if keyword in content_lower:
            return True, description

    return False, ""

def fetch_permit_data(permit_id: str) -> List[Dict[str, Any]]:
    """Fetches HTML with retry logic and Proxy support."""
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    attempt = 0
    
    # Generate a random session ID for this permit request (tries to keep IP consistent for the 3 retries)
    # If 502 happens, we might want to rotate. 
    current_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    
    while attempt < MAX_RETRIES:
        try:
            attempt += 1
            
            # On retry (attempt > 1), generate a NEW session to get a NEW IP
            if attempt > 1:
                current_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
                print(f"  🔄 Rotating IP (Session: {current_session})")
            
            proxies = get_proxy_dict(session_id=current_session)
            
            print(f"  📡 Request URL: {url}")
            if USE_PROXY and attempt == 1:
                print(f"  🛡️  Using Proxy: {PROXY_HOST}")
                
            print(f"  🔄 Attempt {attempt}/{MAX_RETRIES}...", end=" ", flush=True)
            
            # PERFORM REQUEST WITH PROXY
            response = requests.get(
                url, 
                headers=HEADERS, 
                timeout=REQUEST_TIMEOUT, 
                proxies=proxies,
                verify=VERIFY_SSL  # Configurable SSL verification
            )
            
            print(f"Status: {response.status_code}, Size: {len(response.content)} bytes")
            
            # --- IMPROVED 502 HANDLING ---
            if response.status_code == 502:
                print(f"\n  ⚠️  Proxy Gateway Error (502): The proxy connected, but the TARGET refused connection.")
                
                # Check for Bright Data specific headers to know WHY it failed
                bd_error = response.headers.get('x-luminati-error') or response.headers.get('x-brd-error')
                if bd_error:
                    print(f"     🔎 BrightData Reason: {bd_error}")
                else:
                    # Often info is in the body for 502s
                    print(f"     🔎 Body: {response.text[:200]}")
                
                if attempt < MAX_RETRIES:
                    time.sleep(5) 
                    continue
                else:
                    print(f"   ❌ Gave up after {MAX_RETRIES} attempts")
                    return []
            
            is_blocked, block_reason = detect_captcha_blocking(response)
            
            if is_blocked:
                print(f"\n  🚫 CAPTCHA/BLOCKING DETECTED: {block_reason}")
                print(f"  ⏳ PAUSING FOR {CAPTCHA_PAUSE_SECONDS}s...")
                time.sleep(CAPTCHA_PAUSE_SECONDS)
                continue 
            
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            has_meetings = _has_meetings(soup)
            meetings_list = []
            
            if has_meetings:
                print(f"  ✓ Meetings detected, parsing...", end=" ", flush=True)
                meetings_list = _parse_meetings(soup)
                print(f"Found {len(meetings_list)} meetings")
            else:
                print("  ℹ No meetings found")
                
            flat_results = []
            for meeting in meetings_list:
                entry = {
                    'permit_id': permit_id,
                    'meeting_id': meeting.get('meeting_id'),
                    'meeting_date': meeting.get('meeting_date'),
                    'meeting_url': meeting.get('meeting_url'),
                    'essence': meeting.get('essence'),
                    'decision_status': meeting.get('decision_status')
                }
                flat_results.append(entry)
                save_meeting_entry(entry)
                
            return flat_results

        except requests.exceptions.ProxyError as e:
            logger.error(f"Proxy connection error for {permit_id}: {e}")
            print(f"\n  🔌 Proxy Error: {str(e)}")
            if attempt < MAX_RETRIES:
                time.sleep(10)  # Wait before retrying proxy
                continue
            return []
            
        except requests.exceptions.ConnectTimeout as e:
            logger.error(f"Proxy timeout for {permit_id}: {e}")
            print(f"\n  ⏱️  Proxy Timeout: {str(e)}")
            if attempt < MAX_RETRIES:
                time.sleep(10)
                continue
            return []
            
        except requests.exceptions.SSLError as e:
            logger.error(f"SSL error for {permit_id}: {e}")
            error_str = str(e)
            if "CERTIFICATE_VERIFY_FAILED" in error_str or "self signed" in error_str.lower():
                print(f"\n  🔒 SSL Certificate Error: Proxy uses self-signed certificate")
                print(f"   💡 Current VERIFY_SSL setting: {VERIFY_SSL}")
            else:
                print(f"\n  🔒 SSL Error: {str(e)}")
            if attempt < MAX_RETRIES:
                time.sleep(5)
                continue
            return []
            
        except HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None
            print(f"\n  🚫 HTTP ERROR: Status {status_code}")
            time.sleep(5)
            continue
            
        except Exception as e:
            logger.error(f"Error fetching {permit_id}: {e}")
            print(f"\n  ❌ Error: {str(e)}")
            return []
            
    print(f"\n  ❌ Gave up on {permit_id} after {MAX_RETRIES} attempts.")
    return []

# ============================================================================
# FILE OPERATIONS
# ============================================================================

def load_existing_meetings() -> List[Dict[str, Any]]:
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    return json.loads(content)
        except (json.JSONDecodeError, ValueError):
            return []
    return []

def save_meeting_entry(entry: Dict[str, Any]):
    existing_meetings = load_existing_meetings()
    entry_key = (entry.get('permit_id'), entry.get('meeting_id'))
    
    for existing in existing_meetings:
        existing_key = (existing.get('permit_id'), existing.get('meeting_id'))
        if entry_key == existing_key:
            return

    existing_meetings.append(entry)
    
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(existing_meetings, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"Error saving to {OUTPUT_FILE}: {e}")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("Bat Yam Scraper: PROXY EDITION")
    if USE_PROXY:
        print(f"✅ Proxy Enabled")
        print(f"   Host: {PROXY_HOST}:{PROXY_PORT}")
        print(f"   SSL Verification: {'Enabled' if VERIFY_SSL else 'DISABLED (Recommended)'}")
        
        # Test proxy connection before starting
        print("\n🔎 Testing proxy connection...")
        if not test_proxy_connection():
            print("\n⚠️  WARNING: Proxy test failed!")
            print("   Check your PROXY_USER and PROXY_PASS in .env")
            print("   Continuing anyway in 5 seconds...")
            time.sleep(5)
        else:
            print("\n✅ Proxy connected successfully. Starting scrape...")
    else:
        print("⚠️  Proxy Disabled")
    print("=" * 60)

    if not os.path.exists(PERMIT_FILE):
        print(f"ERROR: {PERMIT_FILE} not found.")
        return

    # Load permit IDs from opportunities.json
    try:
        with open(PERMIT_FILE, 'r', encoding='utf-8') as f:
            opportunities_data = json.load(f)
        
        # Extract permit_id from each entry
        permit_ids = []
        for entry in opportunities_data:
            if isinstance(entry, dict) and 'permit_id' in entry:
                permit_id = str(entry['permit_id']).strip()
                if permit_id:  # Only add non-empty permit IDs
                    permit_ids.append(permit_id)
        
        # Remove duplicates while preserving order
        seen = set()
        permit_ids = [pid for pid in permit_ids if pid not in seen and not seen.add(pid)]
        
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse {PERMIT_FILE}: {e}")
        return
    except Exception as e:
        print(f"ERROR: Failed to load {PERMIT_FILE}: {e}")
        return

    print(f"Loaded {len(permit_ids)} permits to process from {PERMIT_FILE}.")
    
    existing_count = len(load_existing_meetings())
    if existing_count > 0:
        print(f"Found {existing_count} existing meetings in {OUTPUT_FILE}")

    total_saved = 0
    current_batch_limit = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
    requests_since_last_pause = 0

    for i, permit_id in enumerate(permit_ids, 1):
        print(f"[{i}/{len(permit_ids)}] Permit {permit_id}:", end=" ", flush=True)
        
        meetings = fetch_permit_data(permit_id)
        
        if meetings:
            print(f"✅ FOUND {len(meetings)} meetings - Saving...", end=" ", flush=True)
            total_saved += len(meetings) # fixed counter logic
            print(f"✓")
        else:
            print("❌") # Simple indicator

        requests_since_last_pause += 1
        
        if requests_since_last_pause >= current_batch_limit:
            pause = random.uniform(LONG_PAUSE_MIN, LONG_PAUSE_MAX)
            print(f"    ☕ Coffee break: Pausing for {pause:.1f}s...")
            time.sleep(pause)
            requests_since_last_pause = 0
            current_batch_limit = random.randint(BATCH_SIZE_MIN, BATCH_SIZE_MAX)
        else:
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            time.sleep(delay)

    print("\n" + "=" * 60)
    print(f"DONE. Total new meetings saved: {total_saved}")
    print(f"Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()