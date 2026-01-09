
import os
import json
import logging
import glob
import sys
import threading
import random
import string
import time
from datetime import datetime
from threading import Lock
import concurrent.futures
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION FROM ANALYZE_PERMITS.PY
# ============================================================================

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

# PROXY CONFIGURATION
USE_PROXY = True
PROXY_HOST = os.getenv("PROXY_HOST", "brd.superproxy.io")
PROXY_PORT = os.getenv("PROXY_PORT", "33335")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
VERIFY_SSL = False

# API
API_URL_TEMPLATE = (
    "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
    "?appname=cixpa&prgname=GetBakashaFile&siteid=81&b={permit_id}&arguments=siteid,b"
)

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://batyam.complot.co.il/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
}

REQUEST_TIMEOUT = 30
MAX_WORKERS = 5 

# Files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERMITS_DATA_DIR = os.path.join(BASE_DIR, "permits_data")
PERMIT_NUMBERS_DIR = os.path.join(BASE_DIR, "permit_numbers")

RELEVANT_PERMITS_FILE = os.path.join(PERMIT_NUMBERS_DIR, "relevant_permits.json")
OPPORTUNITIES_FILE = "opportunities.json"
TEMP_JSONL = os.path.join(PERMITS_DATA_DIR, "daily_update_temp.jsonl")

# Locks
jsonl_lock = Lock()

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("daily_scraper.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# SCRAPING HELPERS (With Local Proxy Logic)
# ============================================================================

def get_proxy_dict(session_id=None):
    if not USE_PROXY:
        return None
    current_user = PROXY_USER
    if not current_user or not PROXY_PASS:
        return None
    if 'brd-customer' in current_user:
        if '-country-' not in current_user:
             current_user = f"{current_user}-country-il"
        if session_id:
            current_user = f"{current_user}-session-{session_id}"
    proxy_url = f"http://{current_user}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
    return {"http": proxy_url, "https": proxy_url}

def get_soup(permit_id: str, max_retries: int = 2):
    """
    Fetches the URL and returns BeautifulSoup object using robust proxy logic.
    """
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=session_id)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, proxies=proxies, verify=VERIFY_SSL)
            if response.status_code == 429:
                wait = 30 * (attempt + 1)
                logger.warning(f"Permit {permit_id}: 429 Limit. Cooling down {wait}s...")
                time.sleep(wait)
                continue
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"Error fetching {permit_id} (Attempt {attempt+1}): {e}")
            time.sleep(2)
            # Rotate proxy on error
            session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
            proxies = get_proxy_dict(session_id=session_id)
            
    return None


# Import parsing logic purely for extraction, NOT fetching
# To avoid double-fetching, we'll import functions or implement simple extractors.
# Importing is better for maintenance but we must ensure we don't accidentally run fetching code.
# The user asked to BASE on analyze_permits and enrich_permits.
# We will duplicate the PARSING calls but use our own FETCHING (get_soup) to ensure we control the proxy/workers.

# But wait, analyze_permits helpers (like _parse_history) take soup. perfect.
try:
    from analyze_permits import _parse_history, _parse_meetings
except ImportError as e:
    logger.error(f"Import Error: {e}")
    sys.exit(1)

def _get_text(el) -> str:
    """Return stripped text from a BeautifulSoup element."""
    if not el:
        return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def parse_requirements_level(soup: BeautifulSoup):  # Returns list[dict] or None
    """
    Parses the 'Requirements Level' from the specific requirements table.
    We target '#table-requirments' (note the typo in source ID).
    Filters only for status 'הושלם' (Completed).
    Returns a list of dictionaries with keys: Phaze, Requirement, Date, Status.
    """
    try:
        # The ID in the HTML is misspelled as 'table-requirments'
        # Crucial fix: The ID might be on the DIV wrapper, not the table itself
        container = soup.find(id='table-requirments')
        if not container:
            container = soup.find(id='table-requirements')
            
        table = None
        if container:
            if container.name == 'table':
                table = container
            else:
                table = container.find('table')
        
        if not table:
            return None

        completed_items = []
        current_phaze = "General"
        
        # Iterate over all rows in the table body (or just table if no tbody)
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
                
            # --- IDENTIFY HEADER (Category/Phaze) ---
            is_header = False
            
            # Check 1: Accordion class
            if row.get('class') and any('accordion' in c for c in row.get('class')):
                is_header = True
            
            # Check 2: Single cell spanning (colspan=4) with strong
            elif len(cells) == 1 and cells[0].has_attr('colspan'):
                is_header = True
                
            # Check 3: Just strong text in a single cell row (fallback)
            elif len(cells) == 1 and cells[0].find('strong'):
                is_header = True

            if is_header:
                current_phaze = _get_text(cells[0])
                # Clean up the "( 12)" count if present at the end
                if current_phaze and '(' in current_phaze and current_phaze.endswith(')'):
                    try:
                        current_phaze = current_phaze.rsplit('(', 1)[0].strip()
                    except:
                        pass
                continue

            # --- IDENTIFY DATA (Requirement) ---
            # Data rows usually have 3+ cells: Req | Status | Date | Comments
            if len(cells) >= 3:
                req_desc = _get_text(cells[0])
                req_status = _get_text(cells[1])
                req_date = _get_text(cells[2])
                
                # Cleanup description
                if req_desc and req_desc.startswith("-"):
                    req_desc = req_desc.lstrip("-").strip()
                
                # FILTER: Only save if status is 'הושלם'
                if req_status == "הושלם":
                    completed_items.append({
                        "Phaze": current_phaze,
                        "Requirement": req_desc,
                        "Date": req_date,
                        "Status": req_status
                    })

        if not completed_items:
            return None
            
        return completed_items

    except Exception as e:
        logger.warning(f"Error parsing requirements level: {e}")
    
    return None

# ============================================================================
# MAIN LOGIC
# ============================================================================

def find_latest_json() -> str:
    """Finds the most recent bat_yam_permits_data JSON file in permits_data directory."""
    if not os.path.exists(PERMITS_DATA_DIR):
        return None
        
    files = glob.glob(os.path.join(PERMITS_DATA_DIR, "bat_yam_permits_data_*.json"))
    if not files:
        return None
    files.sort()
    return files[-1]

def load_json(path: str):
    if not os.path.exists(path):
        return []
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_relevant_ids() -> list:
    if not os.path.exists(RELEVANT_PERMITS_FILE):
        return []
    try:
        with open(RELEVANT_PERMITS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                return [str(item).strip() for item in data]
    except Exception as e:
        logger.error(f"Failed to load relevant IDs from {RELEVANT_PERMITS_FILE}: {e}")
    return []

def save_incremental(data: dict):
    """Saves a single record to the JSONL file safely."""
    if not data: return
    try:
        json_line = json.dumps(data, ensure_ascii=False) + '\n'
        with jsonl_lock:
            with open(TEMP_JSONL, 'a', encoding='utf-8') as f:
                f.write(json_line)
    except Exception as e:
        logger.error(f"Failed to save incremental JSONL: {e}")

def scrape_and_save(permit_data: dict):
    """
    Scrapes updates for a permit and saves the fulled updated object to JSONL.
    """
    permit_id = str(permit_data.get('permit_id'))
    if not permit_id: return

    logger.info(f"🔄 Updating {permit_id}...")
    try:
        soup = get_soup(permit_id)
        if not soup:
            # Failed to fetch, keep old data
            logger.warning(f"Using old data for {permit_id}")
            save_incremental(permit_data)
            return False

        # Extract updates
        # 1. History
        history = _parse_history(soup)
        
        # 2. Meetings
        meeting_history = _parse_meetings(soup) if soup.text and "ישיבות" in soup.text else [] # simple check, _parse_meetings does more
        
        # 3. Requirements Level
        req_level = parse_requirements_level(soup)
        
        updates = {
            "history": history,
            "meeting_history": meeting_history,
            "requirements_level": req_level
        }
        
        # Merge updates
        permit_data.update(updates)
        save_incremental(permit_data)
        return True
        
    except Exception as e:
        logger.error(f"❌ Error scraping {permit_id}: {e}")
        save_incremental(permit_data)
        return False

def convert_jsonl_to_json(jsonl_file: str, output_file: str):
    logger.info(f"Converting {jsonl_file} to {output_file}...")
    if not os.path.exists(jsonl_file):
        logger.error("JSONL file not found for conversion.")
        return

    data_map = {}
    try:
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        item = json.loads(line)
                        pid = str(item.get('permit_id'))
                        data_map[pid] = item
                    except:
                        pass
    except Exception as e:
        logger.error(f"Error reading JSONL: {e}")
        return

    # Define standard key order to match existing JSON files
    key_order = [
        "is_relevant", "permit_id", "project_type", "description", "num_units", 
        "key_features", "request_type", "main_use", "request_description", 
        "address", "applicants", "parcels", "history", "meeting_history", 
        "request_date", "requirements_level"
    ]
    
    # Helper for sorting keys
    def _parse_date(d_str):
        if not d_str: return datetime.min
        try:
            return datetime.strptime(d_str, "%d/%m/%Y")
        except:
            return datetime.min

    final_list = []
    for item in data_map.values():
        # --- SORTING LOGIC ---
        # 1. Sort History (Newest first)
        if item.get('history') and isinstance(item['history'], list):
            item['history'].sort(key=lambda x: _parse_date(x.get('event_date')), reverse=True)
            
        # 2. Sort Requirements Level (Newest first)
        if item.get('requirements_level') and isinstance(item['requirements_level'], list):
            item['requirements_level'].sort(key=lambda x: _parse_date(x.get('Date')), reverse=True)

        # Create ordered dict
        ordered_item = {k: item.get(k) for k in key_order if k in item}
        # Add any other keys that might exist but aren't in the standard list (at the end)
        for k, v in item.items():
            if k not in ordered_item:
                ordered_item[k] = v
        final_list.append(ordered_item)
    
    # 3. Sort Main List by Request Date (Newest first)
    final_list.sort(key=lambda x: _parse_date(x.get('request_date')), reverse=True)
    
    # Optional: Sort by permit_id or some other metric if needed, but dict order is undefined usually.
    # We'll just dump it.
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
        
    logger.info(f"✅ Saved {len(final_list)} permits to {output_file}")
    
    if os.path.exists(jsonl_file):
        os.remove(jsonl_file)
        logger.info("Deleted temporary JSONL file.")

def main():
    logger.info("🚀 Starting Daily Permit Scraper (Workers + Proxy + JSONL)")
    
    latest_file = find_latest_json()
    if not latest_file:
        logger.error("No base JSON file found.")
        return
        
    logger.info(f"Base file: {latest_file}")
    base_data = load_json(latest_file)
    relevant_ids = set(load_relevant_ids())
    logger.info(f"Relevant IDs to update: {len(relevant_ids)}")
    
    # Check if TEMP_JSONL exists
    if os.path.exists(TEMP_JSONL):
         # If existing, user might want to resume or clear.
         # For safety, we keep it but warn.
         logger.warning(f"Found existing {TEMP_JSONL} - appending new results to it.")
    
    if not os.path.exists(PERMITS_DATA_DIR):
        os.makedirs(PERMITS_DATA_DIR)

    today_str = datetime.now().strftime("%Y_%m_%d")
    output_filename = os.path.join(PERMITS_DATA_DIR, f"bat_yam_permits_data_{today_str}.json")
    
    processed_ids = set()

    # Worker Pool
    logger.info(f"Starting ThreadPoolExecutor with {MAX_WORKERS} workers...")
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = []
        
        # 1. Process Base Data
        for item in base_data:
            if not isinstance(item, dict): continue
            pid = str(item.get('permit_id'))
            processed_ids.add(pid)
            
            if pid in relevant_ids:
                futures.append(executor.submit(scrape_and_save, item))
            else:
                futures.append(executor.submit(save_incremental, item))
                
        # 2. Process New Opportunities
        if os.path.exists(OPPORTUNITIES_FILE):
            ops = load_json(OPPORTUNITIES_FILE)
            for item in ops:
                if not isinstance(item, dict): continue
                pid = str(item.get('permit_id'))
                if pid not in processed_ids:
                    logger.info(f"Found NEW opportunity {pid}")
                    futures.append(executor.submit(save_incremental, item))
                    processed_ids.add(pid)
        
        # Wait for completion
        completed = 0
        total = len(futures)
        for future in concurrent.futures.as_completed(futures):
            completed += 1
            if completed % 10 == 0:
                logger.info(f"Progress: {completed}/{total}")

    logger.info("All tasks completed.")
    convert_jsonl_to_json(TEMP_JSONL, output_filename)
    
    # Cleaning opportunities.json for next use
    try:
        if os.path.exists(OPPORTUNITIES_FILE):
             with open(OPPORTUNITIES_FILE, 'w', encoding='utf-8') as f:
                 f.write("[]")
             logger.info(f"🧹 Cleaned {OPPORTUNITIES_FILE} for next use.")
    except Exception as e:
        logger.error(f"Failed to clean {OPPORTUNITIES_FILE}: {e}")

    logger.info("Done.")

if __name__ == "__main__":
    main()
