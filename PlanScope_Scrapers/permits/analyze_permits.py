"""
Stage 2 & 3: API Data Retrieval + AI Filtering Pipeline

This script reads permit IDs from permit_numbers.txt, fetches the "מהות הבקשה" 
(Request Intention) field from the Bat Yam API, and uses GPT-5-mini to identify
investor-relevant opportunities like Tama 38, Pinui Binui, and new developments.

Usage:
    1. Create .env file with: OPENAI_API_KEY=your-key-here
    2. pip install -r requirements.txt
    3. python analyze_permits.py
"""

import os
import json
import time
import random
import re
import logging
import string
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv
import urllib3

# Suppress SSL warnings since verify=False is often needed for proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables from /Users/yotamcohen/Desktop/PlanScope/.env or .env.example
# Path goes 3 levels up: permits/ -> PlanScope_Scrapers/ -> PlanScope/
base_dir = Path(__file__).parent.parent.parent
env_path = base_dir / '.env'
env_example_path = base_dir / '.env.example'

if env_path.exists():
    load_dotenv(env_path)
    print(f"✅ Loaded environment from: {env_path}")
elif env_example_path.exists():
    load_dotenv(env_example_path)
    print(f"⚠️  Loaded environment from EXAMPLE file: {env_example_path}")
else:
    print(f"⚠️  No .env file found at {base_dir}")
    print("   Relying on system environment variables.")

# ============================================================================
# PROXY CONFIGURATION
# ============================================================================

USE_PROXY = True  # שנה ל-False אם אתה רוצה לעבוד בלי פרוקסי

# פרטי הפרוקסי (קבל אותם מהדשבורד של Bright Data / הספק שלך)
PROXY_HOST = os.getenv("PROXY_HOST", "zproxy.lum-superproxy.io")
PROXY_PORT = os.getenv("PROXY_PORT", "22225")  # Default Bright Data residential port

# טעינת שם המשתמש והסיסמה משתני הסביבה
# For Bright Data, username format is usually: brd-customer-{customer_id}-zone-{zone_name}
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# SSL Verification setting
VERIFY_SSL = False

# ============================================================================
# END OF PROXY CONFIGURATION
# ============================================================================

# API endpoint template
API_URL_TEMPLATE = (
    "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
    "?appname=cixpa&prgname=GetBakashaFile&siteid=81&b={permit_id}&arguments=siteid,b"
)

# Request headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://batyam.complot.co.il/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Rate limiting configuration
REQUEST_DELAY_MIN = 2.0  # Minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 5.0  # Maximum delay between requests (seconds)
BATCH_SIZE = 10          # Number of requests before cooldown
BATCH_COOLDOWN = 20      # Cooldown duration after batch (seconds)

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Files
PERMIT_FILE = "permit_numbers.txt"
OUTPUT_FILE = "opportunities.json"
ERROR_LOG_FILE = "errors.log"
DEBUG_REQUESTS_FILE = "model_requests.txt"

# LLM System Prompt for investor opportunity analysis
SYSTEM_PROMPT = """You are a real estate investment analyst specializing in Israeli construction permits.

You will receive the "מהות הבקשה" (Request Intention) text from a Bat Yam building permit. Analyze it and determine if it represents a valuable investment opportunity.

CRITICAL SEMANTIC INSTRUCTION:
Focus on both the ACTION (e.g., "Building", "Constructing") and the OBJECT/ASSET (e.g., "Office Tower", "4 Residential Buildings").
If the text mentions a major asset type (like a new building, tower, or complex) as the subject of the request, treat it as RELEVANT even if the specific verb "construction" is missing or implied.

RELEVANT OPPORTUNITIES include:

1. Residential Projects & Expansions:
- תמ"א 38 (Tama 38) - earthquake reinforcement with added units
- פינוי בינוי (Pinui Binui) - demolition and reconstruction
- הריסה ובנייה (Demolition and Construction)
- New residential projects (e.g., "Residential complex", "New apartments")
- מגדל מגורים (Residential tower) - mention of the tower itself
- Addition of floors or significant expansions
- Major renovations creating new residential units
- Destruction and construction of new buildings

2. Commercial, Employment & Mixed-Use Assets:
- Mixed-use developments (e.g., Residential + Commercial)
- Office Buildings: Office towers, business centers, corporate hubs (e.g., "4 Office buildings", "Employment center").
- Industrial Buildings: Logistics centers, factories, warehouses, and industrial parks.
- Employment Centers: High-tech parks and specialized commercial zones.

3. Major Infrastructure:
- Big upgrades to infrastructures, public transportation, and environmental upgrades.

GENERAL RULE FOR RELEVANCE:
Any permit that implies the creation, establishment, or existence of a new standalone structure, a new wing, or a major complex is RELEVANT.
NOT RELEVANT (ignore):
Treat as NOT relevant any permit that describes only small, non-value-adding work and does NOT include major construction/expansion or creation of new residential/commercial units.
Examples: balcony closure, pergola, signs, small repairs/minor renovations, interior-only changes, storage room, fence, AC/ventilation installations, sealing changes, accessibility ramps (unless part of a larger project)

OUTPUT FORMAT (JSON only, no markdown, no code blocks):
{
  "is_relevant": true,
  "permit_id": "...",
  "project_type": "Tama 38 / Pinui Binui / New Construction / Mixed-Use / etc.",
  "description": "copy the Hebrew description text",
  "num_units": "number of residential units if mentioned (יח\"ד), otherwise null",
  "key_features": ["list", "key", "points"]
}

If NOT relevant:
{
  "is_relevant": false,
  "permit_id": "...",
  "reason": "brief explanation"
}"""

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Configure logging
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
# FUNCTIONS
# ============================================================================

def get_proxy_dict(session_id=None):
    """
    Builds the proxy dictionary for requests.
    """
    if not USE_PROXY:
        return None
    
    current_user = PROXY_USER
    
    # בדיקה שהמשתמש הזין פרטים
    if not current_user or not PROXY_PASS:
        print("⚠️  Error: Proxy is enabled but PROXY_USER or PROXY_PASS are missing from .env!")
        return None
    
    # Bright Data Logic: Force Israel targeting and Session rotation
    if 'brd-customer' in current_user:
        # Force Israel targeting if not already in username
        if '-country-' not in current_user:
             current_user = f"{current_user}-country-il"
        
        # IP Rotation Logic
        if session_id:
            current_user = f"{current_user}-session-{session_id}"

    # Construct the URL with authentication
    proxy_url = f"http://{current_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    
    return {
        "http": proxy_url,
        "https": proxy_url,
    }


def test_proxy_connection():
    """Test if proxy is working."""
    if not USE_PROXY:
        return True
    
    # Use a random session for the test to ensure we get a fresh IP
    rand_session = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=rand_session)
    
    if not proxies:
        return False

    print(f"   Testing connection to {PROXY_HOST}...")
    
    try:
        # Test with a simple request to check IP
        test_response = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=20,
            verify=VERIFY_SSL
        )
        if test_response.status_code == 200:
            ip_info = test_response.json()
            origin_ip = ip_info.get('origin')
            print(f"   ✅ Proxy Connected! External IP: {origin_ip}")
            return True
        else:
            print(f"   ⚠️  Proxy test returned status {test_response.status_code}")
            return False

    except requests.exceptions.ProxyError as e:
        print(f"   ❌ Proxy Error: Failed to connect. Check Host/Port/User/Pass.")
        print(f"      Details: {e}")
        return False
    except requests.exceptions.SSLError as e:
        print(f"   ❌ SSL Error. Try setting VERIFY_SSL = False.")
        return False
    except Exception as e:
        print(f"   ❌ Connection failed: {e}")
        return False


def _get_text(el) -> Optional[str]:
    """Return stripped text from a BeautifulSoup element, cleaned of control characters."""
    if not el:
        return None
    txt = el.get_text(separator=" ", strip=True)
    # Clean up invisible Unicode control characters (RLM U+200F, LRM U+200E)
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


def _parse_request_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    info_table = soup.select_one("#info-main table tbody")
    if not info_table:
        return {"request_type": None, "main_use": None, "request_description": None}

    rows = info_table.select("tr")
    # Get the second td (index 1) which contains the value, not the label (first td)
    # Row 2 = סוג הבקשה (request type), Row 3 = שימוש עיקרי (main use), Row 4 = תיאור הבקשה (request description)
    request_type = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    main_use = _get_text(rows[3].find_all("td")[1]) if len(rows) >= 4 and len(rows[3].find_all("td")) > 1 else None
    request_description = _get_text(rows[4].find_all("td")[1]) if len(rows) >= 5 and len(rows[4].find_all("td")) > 1 else None
    return {"request_type": request_type, "main_use": main_use, "request_description": request_description}


def _parse_address(soup: BeautifulSoup) -> Optional[str]:
    # Address is in the 4th h5 element inside #navbar-titles-id
    # Structure: h5[0]=label, h5[1]=permit#, h5[2]=label "כתובת:", h5[3]=actual address
    navbar = soup.select_one("#navbar-titles-id")
    if navbar:
        h5_elements = navbar.find_all("h5")
        # Get the 4th h5 (index 3) which contains the address
        if len(h5_elements) >= 4:
            return _get_text(h5_elements[3])
    
    # Fallback: try col-md-4 div which contains address
    address = soup.select_one("#navbar-titles-id .col-md-4 h5")
    return _get_text(address)


def _parse_applicants(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    table = soup.select_one("#table-baaley-inyan table tbody")
    if not table:
        return {"requestor": None, "owner": None, "author": None}

    rows = table.select("tr")
    requestor = _get_text(rows[0].find_all("td")[1]) if len(rows) >= 1 and len(rows[0].find_all("td")) > 1 else None
    owner = _get_text(rows[1].find_all("td")[1]) if len(rows) >= 2 and len(rows[1].find_all("td")) > 1 else None
    author = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    return {"requestor": requestor, "owner": owner, "author": author}


def _parse_parcels(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    parcels = []
    table = soup.select_one("#table-gushim-helkot table tbody")
    if not table:
        return parcels

    for row in table.select("tr"):
        tds = row.find_all("td")
        # Structure: td[0]=empty/link, td[1]=gush, td[2]=helka
        if len(tds) >= 3:
            gush = _get_text(tds[1])
            helka = _get_text(tds[2])
            parcels.append({"gush": gush, "helka": helka})
    return parcels


def _parse_history(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    history = []
    table = soup.select_one("#table-events table tbody")
    if not table:
        return history

    for row in table.select("tr"):
        tds = row.find_all("td")
        if not tds:
            continue
        event_type = _get_text(tds[0]) if len(tds) > 0 else None
        event_description = _get_text(tds[1]) if len(tds) > 1 else None
        event_date = _get_text(tds[2]) if len(tds) > 2 else None
        event_end_date = _get_text(tds[3]) if len(tds) > 3 else None
        history.append({
            "event_type": event_type,
            "event_description": event_description,
            "event_date": event_date,
            "event_end_date": event_end_date,
        })
    return history


def fetch_permit_data(permit_id: str, max_retries: int = 2) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Fetch HTML from API and extract:
      - "מהות הבקשה" text (mahut_text)
      - request type, main use
      - address
      - applicants (requestor/owner/author)
      - parcels (gush/helka)
      - events history
    
    Includes CAPTCHA detection and retry logic.
    
    Args:
        permit_id: The permit number to fetch
        max_retries: Maximum number of retry attempts for CAPTCHA (default: 2)
        
    Returns:
        (mahut_text, metadata_dict)
    """
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    
    # Generate a random session ID for proxy rotation
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=session_id)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, proxies=proxies, verify=VERIFY_SSL)
            response.raise_for_status()
            
            # Ensure proper encoding for Hebrew text
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the div#mahut element containing "מהות הבקשה"
            mahut_div = soup.find('div', id='mahut')
            
            if mahut_div:
                # Get the text content, cleaned up
                text = mahut_div.get_text(separator=' ', strip=True)
                # Remove the header "מהות הבקשה" from the beginning if present
                text = text.replace('מהות הבקשה', '', 1).strip()
                # Clean up invisible Unicode control characters (RLM, LRM, etc.)
                text = text.replace('\u200f', '').replace('\u200e', '').strip()
                mahut_text = text if text else None
            else:
                # CAPTCHA detected - div#mahut not found
                if attempt < max_retries:
                    logger.warning(f"Permit {permit_id}: CAPTCHA detected (div#mahut not found), waiting 40s before retry {attempt + 1}/{max_retries}...")
                    print(f"\n🤖 CAPTCHA detected! Waiting 40 seconds before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(40)
                    continue
                else:
                    logger.error(f"Permit {permit_id}: div#mahut not found after {max_retries + 1} attempts (likely CAPTCHA)")
                    return None, {}

            # Parse additional metadata
            request_info = _parse_request_info(soup)
            address = _parse_address(soup)
            applicants = _parse_applicants(soup)
            parcels = _parse_parcels(soup)
            history = _parse_history(soup)
            
            # Parse meeting history
            meeting_history = []
            if _has_meetings(soup):
                meeting_history = _parse_meetings(soup)

            metadata = {
                "request_type": request_info.get("request_type"),
                "main_use": request_info.get("main_use"),
                "request_description": request_info.get("request_description"),
                "address": address,
                "applicants": applicants,
                "parcels": parcels,
                "history": history,
                "meeting_history": meeting_history,
            }

            return mahut_text, metadata
                
        except requests.exceptions.Timeout:
            logger.error(f"Permit {permit_id}: Request timeout after {REQUEST_TIMEOUT}s")
            return None, {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Permit {permit_id}: Request failed - {e}")
            return None, {}
        except Exception as e:
            logger.error(f"Permit {permit_id}: Unexpected error - {e}")
            return None, {}
    
    return None, {}  # Shouldn't reach here, but just in case


def log_model_request(permit_id: str, user_content: str):
    """
    Log the request being sent to the model for debugging.
    
    Args:
        permit_id: The permit ID
        user_content: The user message content being sent
    """
    # Use absolute path to ensure file is written to the correct location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(script_dir, DEBUG_REQUESTS_FILE)
    
    # Clean up invisible Unicode control characters (RLM, LRM, etc.)
    cleaned_content = user_content.replace('\u200f', '').replace('\u200e', '')
    
    try:
        with open(log_file_path, 'a', encoding='utf-8-sig') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ID: {permit_id}\n")
            f.write(f"Request:\n{cleaned_content}\n")
            f.write("=" * 80 + "\n\n")
            f.flush()  # Force write to disk immediately
            os.fsync(f.fileno())  # Force OS to write to disk
    except Exception as e:
        logger.error(f"Failed to write to debug file: {e}")
        print(f"ERROR: Could not write to {log_file_path}: {e}")


def analyze_with_ai(mahut_text: str, permit_id: str, client: OpenAI, max_retries: int = 3) -> Optional[dict]:
    """
    Send "מהות הבקשה" text to GPT-5-mini for investor opportunity analysis.
    Includes retry logic with exponential backoff for transient failures.
    
    Args:
        mahut_text: The extracted request intention text
        permit_id: The permit ID for reference
        client: OpenAI client instance
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Parsed JSON response from LLM, or None if analysis fails after all retries
    """
    for attempt in range(max_retries):
        try:
            user_content = f"Permit ID: {permit_id}\n\nמהות הבקשה:\n{mahut_text}"
            
            # Log the request being sent to the model (only on first attempt)
            if attempt == 0:
                log_model_request(permit_id, user_content)
            
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract the response text
            response_text = (response.choices[0].message.content or "").strip()
            if not response_text:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Permit {permit_id}: Empty response (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Permit {permit_id}: AI returned empty response after {max_retries} attempts")
                    return None
            
            # Clean up potential markdown code blocks
            if response_text.startswith('```'):
                # Remove ```json and ``` markers
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Ensure permit_id is in the result
            result['permit_id'] = permit_id
            
            return result
            
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Permit {permit_id}: JSON parse error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Permit {permit_id}: Failed to parse AI response as JSON after {max_retries} attempts - {e}")
                logger.debug(f"Raw response: {response_text if 'response_text' in locals() else 'N/A'}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Permit {permit_id}: AI call failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Permit {permit_id}: AI analysis failed after {max_retries} attempts - {e}")
                return None
    
    return None  # Shouldn't reach here, but just in case


def load_processed_permits(processed_file: str = "processed_permits.txt") -> set:
    """
    Load already-processed permit IDs to enable resume (includes both relevant and non-relevant).
    
    Args:
        processed_file: Path to file containing all processed permit IDs
        
    Returns:
        Set of permit IDs that have already been processed
    """
    if not os.path.exists(processed_file):
        return set()
    
    processed = set()
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            for line in f:
                permit_id = line.strip()
                if permit_id:
                    processed.add(permit_id)
        logger.info(f"Loaded {len(processed)} already-processed permits from {processed_file}")
    except Exception as e:
        logger.warning(f"Could not load processed permits: {e}")
    
    return processed


def mark_permit_processed(permit_id: str, processed_file: str = "processed_permits.txt"):
    """
    Mark a permit as processed (regardless of relevance) to enable resume.
    
    Args:
        permit_id: The permit ID to mark as processed
        processed_file: Path to file tracking all processed permits
    """
    try:
        with open(processed_file, 'a', encoding='utf-8') as f:
            f.write(f"{permit_id}\n")
    except Exception as e:
        logger.error(f"Failed to mark {permit_id} as processed: {e}")


def save_opportunity_incremental(opportunity: Dict[str, Any], output_file: str = "opportunities.json", relevant_file: str = "relevant_permits.txt"):
    """
    Save a single relevant opportunity to JSON file immediately (incremental save).
    Also append the permit ID to relevant_permits.txt for resume capability.
    
    Args:
        opportunity: Dictionary containing permit data
        output_file: Path to JSON file
        relevant_file: Path to file tracking processed relevant permits
    """
    permit_id = opportunity.get('permit_id', 'unknown')
    
    # Load existing opportunities
    opportunities = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                opportunities = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not load existing {output_file}, starting fresh")
            opportunities = []
    
    # Append new opportunity
    opportunities.append(opportunity)
    
    # Save back to JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved permit {permit_id} to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save opportunity {permit_id}: {e}")
    
    # Append to relevant_permits.txt for resume capability
    try:
        with open(relevant_file, 'a', encoding='utf-8') as f:
            f.write(f"{permit_id}\n")
    except Exception as e:
        logger.error(f"Failed to append {permit_id} to {relevant_file}: {e}")


def main():
    """
    Main workflow: read permits, fetch data, analyze with AI, save results.
    """
    print("=" * 60)
    print("Bat Yam Building Permit Analyzer - Stage 2 & 3")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_api_key_here' or api_key == 'sk-your-api-key-here':
        print("\nERROR: OPENAI_API_KEY not configured!")
        print("   Please create a .env file with:")
        print("   OPENAI_API_KEY=sk-your-actual-api-key")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    print("OK: OpenAI client initialized")
    
    # Test proxy connection
    print(f"Proxy Configured: {USE_PROXY}")
    if USE_PROXY:
        if not test_proxy_connection():
            print("\n❌ Proxy Connection FAILED.")
            print("   Please check your .env file credentials.")
            print("   Continuing without proxy might result in blocking...\n")
            # uncomment next line to stop on error
            # return
    
    # Initialize debug requests file (clear previous content)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(script_dir, DEBUG_REQUESTS_FILE)
    try:
        with open(log_file_path, 'w', encoding='utf-8-sig') as f:
            f.write("Model Requests Debug Log\n")
            f.write("=" * 80 + "\n\n")
        print(f"OK: Debug log initialized: {log_file_path}")
    except Exception as e:
        logger.warning(f"Failed to initialize debug file: {e}")
    
    # Read permit IDs from file
    try:
        with open(PERMIT_FILE, 'r', encoding='utf-8') as f:
            permit_ids = [line.strip() for line in f if line.strip()]
        print(f"OK: Loaded {len(permit_ids)} permit IDs from {PERMIT_FILE}")
    except FileNotFoundError:
        print(f"\nERROR: {PERMIT_FILE} not found!")
        print("   Run the scraper first: python get_bakasha_numbers.py")
        return
    
    # Load already-processed permits for resume capability
    already_processed = load_processed_permits("processed_permits.txt")
    if already_processed:
        print(f"OK: Resume mode - {len(already_processed)} permits already processed")
        permit_ids_to_process = [pid for pid in permit_ids if pid not in already_processed]
        skipped_count = len(permit_ids) - len(permit_ids_to_process)
        print(f"OK: Skipping {skipped_count} already-processed permits")
        permit_ids = permit_ids_to_process
    
    if not permit_ids:
        print("\n" + "=" * 60)
        print("All permits already processed! Nothing to do.")
        print("=" * 60)
        return
    
    # Initialize results
    errors = []
    processed = 0
    relevant_count = 0
    requests_in_batch = 0  # Counter for batch cooldown
    
    print(f"\nProcessing {len(permit_ids)} permits...")
    print("-" * 60)
    
    # Process each permit
    for i, permit_id in enumerate(permit_ids, 1):
        print(f"[{i}/{len(permit_ids)}] Processing permit {permit_id}...", end=" ")
        
        # Fetch data from API
        mahut_text, metadata = fetch_permit_data(permit_id)
        
        if not mahut_text:
            print("ERROR: Failed to fetch")
            errors.append({
                'permit_id': permit_id,
                'error': 'Failed to fetch or extract מהות הבקשה'
            })
            mark_permit_processed(permit_id)  # Mark as processed even if failed
            # Smart throttle: random delay
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            time.sleep(delay)
            requests_in_batch += 1
            continue
        
        # Analyze with AI
        result = analyze_with_ai(mahut_text, permit_id, client)
        
        if result is None:
            print("ERROR: AI analysis failed")
            errors.append({
                'permit_id': permit_id,
                'error': 'AI analysis failed'
            })
            mark_permit_processed(permit_id)  # Mark as processed even if failed
        elif result.get('is_relevant', False):
            project_type = result.get('project_type', 'Unknown')
            try:
                print(f"OK: RELEVANT - {project_type}")
            except UnicodeEncodeError:
                print(f"OK: RELEVANT (permit {permit_id})")
            # Attach parsed metadata
            enriched = {**result, **metadata}
            
            # Save immediately (incremental save)
            save_opportunity_incremental(enriched, OUTPUT_FILE, "relevant_permits.txt")
            relevant_count += 1
            mark_permit_processed(permit_id)  # Mark as processed
        else:
            reason = result.get('reason', 'Not relevant')
            # Encode reason safely for console (Windows console can't handle Hebrew)
            try:
                print(f"SKIP: Not relevant - {reason[:40]}...")
            except UnicodeEncodeError:
                print(f"SKIP: Not relevant (permit {permit_id})")
            mark_permit_processed(permit_id)  # Mark as processed
        
        processed += 1
        requests_in_batch += 1
        
        # Smart throttle: random delay between requests
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        
        # Batch cooldown: every 10 requests, take a longer break
        if requests_in_batch >= BATCH_SIZE and i < len(permit_ids):
            print(f"\n⏸️  Batch cooldown: Processed {BATCH_SIZE} requests, pausing for {BATCH_COOLDOWN}s to avoid blocking...")
            time.sleep(BATCH_COOLDOWN)
            requests_in_batch = 0  # Reset counter
            print("✅ Cooldown complete, resuming...\n")
    
    # Save results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    # Opportunities were saved incrementally during processing
    print(f"OK: All relevant permits saved incrementally to {OUTPUT_FILE}")
    print(f"OK: Relevant permit IDs tracked in relevant_permits.txt")
    
    # Summary
    print(f"\nSummary:")
    print(f"  - Total permits processed: {processed}")
    print(f"  - Investor opportunities found: {relevant_count}")
    print(f"  - Errors: {len(errors)}")
    
    # Show opportunities from file
    if relevant_count > 0:
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                saved_opportunities = json.load(f)
            print(f"\nTop Opportunities:")
            for opp in saved_opportunities[-5:]:  # Show last 5 from this run
                try:
                    print(f"  - {opp['permit_id']}: {opp.get('project_type', 'N/A')}")
                    if opp.get('num_units'):
                        print(f"    Units: {opp['num_units']}")
                except UnicodeEncodeError:
                    print(f"  - {opp['permit_id']} (see opportunities.json for details)")
        except Exception as e:
            logger.warning(f"Could not read opportunities for summary: {e}")


if __name__ == "__main__":
    main()

