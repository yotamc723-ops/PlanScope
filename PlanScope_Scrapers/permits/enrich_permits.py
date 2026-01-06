"""
Script to enrich existing opportunities in opportunities.json with 'request_date' and 'requirements_table'.
Does NOT use LLM. Uses the same proxy and threading logic as analyze_permits.py.
Updated: 
1. Normalizes status to 'הושלם'/'לא הושלם'.
2. Saves 'requirements_table' in a compact, single-line format.
"""

import os
import json
import time
import random
import re
import logging
import string
import threading
import concurrent.futures
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv
import urllib3

# Suppress SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# CONFIGURATION
# ============================================================================

base_dir = Path(__file__).parent.parent.parent
env_path = base_dir / '.env'
env_example_path = base_dir / '.env.example'

if env_path.exists():
    load_dotenv(env_path)
elif env_example_path.exists():
    load_dotenv(env_example_path)

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

# Files
OUTPUT_FILE = "opportunities.json"

# Locks
file_lock = threading.Lock()
print_lock = threading.Lock()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS
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

def _get_text(el) -> Optional[str]:
    if not el: return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def normalize_status(status_text: Optional[str]) -> Optional[str]:
    """
    Normalizes status to 'הושלם' or 'לא הושלם'.
    """
    if not status_text:
        return None
    
    clean = status_text.replace('\u200f', '').replace('\u200e', '').strip()
    
    # Check for "not completed" logic first
    if "לא" in clean:
        return "לא הושלם"
    # Check for "completed" logic
    if "הושלם" in clean:
        return "הושלם"
        
    return clean

def parse_request_date(soup: BeautifulSoup) -> Optional[str]:
    """
    Finds the Request Date (תאריך הגשה) using Regex for robustness.
    """
    # Strategy 1: Find element containing "תאריך הגשה" and regex the date from it or its next sibling
    target_elements = soup.find_all(string=re.compile(r"תאריך הגשה"))
    
    for elem in target_elements:
        text = elem.strip()
        parent_text = elem.parent.get_text(" ", strip=True) if elem.parent else ""
        combined_text = text + " " + parent_text
        
        if elem.parent:
            next_sib = elem.parent.find_next_sibling()
            if next_sib:
                combined_text += " " + next_sib.get_text(" ", strip=True)
                
        match = re.search(r"(\d{2}/\d{2}/\d{4})", combined_text)
        if match:
            return match.group(1)
            
    # Strategy 2: Global search in the top area text
    top_info = soup.find(class_='top-navbar-info-desc') 
    if top_info:
        match = re.search(r"תאריך הגשה.*?(\d{2}/\d{2}/\d{4})", top_info.get_text(" ", strip=True))
        if match:
            return match.group(1)
    
    return None

def parse_requirements_level(soup: BeautifulSoup) -> Optional[str]:
    """
    Parses the requirements table to find the 'level' of the permit.
    The level is defined as the Category Name under which the *last* completed ("הושלם") requirement appears.
    """
    req_div = soup.find(id='table-requirments')
    if not req_div:
        req_div = soup.find(id='requirments')
        
    if not req_div:
        return None
        
    table = req_div.find('table')
    if not table:
        return None

    # Handle both tbody and direct tr structure
    tbody = table.find('tbody')
    rows = tbody.find_all('tr') if tbody else table.find_all('tr')
    
    current_category = None
    last_completed_category = None
    
    for row in rows:
        # Check if it's a category row (usually has colspan=4)
        tds = row.find_all('td')
        if len(tds) == 1 and tds[0].get('colspan') == '4':
            # It's a category header
            cat_text = _get_text(tds[0])
            if cat_text:
                # Remove parenthesized counts: "Name (3)" -> "Name"
                current_category = re.sub(r'\s*\(\s*\d+\s*\)$', '', cat_text).strip()
            continue
            
        # Check if it's a data row (4 cells usually)
        if len(tds) >= 3: 
            status = _get_text(tds[1])
            normalized = normalize_status(status)
            
            if normalized == "הושלם":
                last_completed_category = current_category
                
    return last_completed_category

def fetch_extra_data(permit_id: str, max_retries: int = 2) -> Dict[str, Any]:
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=session_id)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, proxies=proxies, verify=VERIFY_SSL)
            if response.status_code == 429:
                time.sleep(30 * (attempt + 1))
                continue
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            return {
                "request_date": parse_request_date(soup),
                "requirements_level": parse_requirements_level(soup)
            }

        except Exception as e:
            time.sleep(2)
            if attempt == max_retries:
                return {"request_date": None, "requirements_level": None}
                
    return {"request_date": None, "requirements_level": None}

def process_permit_enrichment(permit_data: Dict[str, Any], results: Dict[str, int]) -> Dict[str, Any]:
    permit_id = permit_data.get('permit_id')
    if not permit_id:
        return permit_data
        
    try:
        extra_data = fetch_extra_data(permit_id)
        permit_data['request_date'] = extra_data['request_date']
        permit_data['requirements_level'] = extra_data['requirements_level']
        # Remove old key if exists
        permit_data.pop('requirements_table', None)
        
        with print_lock:
            level_str = extra_data['requirements_level'] or "N/A"
            date_str = extra_data['request_date'] or "N/A"
            # Truncate level string for logging
            if len(level_str) > 20: level_str = level_str[:20] + "..."
            print(f"✅ [{permit_id}] Enriched: Date={date_str}, Level={level_str}")
            
        with results['lock']:
            results['processed'] += 1
    except Exception as e:
        logger.error(f"Failed to enrich {permit_id}: {e}")
        with results['lock']:
            results['errors'] += 1
            
    return permit_data

def save_json(data: List[Dict[str, Any]], filename: str):
    """
    Saves the data list to JSON efficiently.
    """
    if not data: return
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def main():
    print("🚀 Starting Permit Enrichment Scraper (Date & Requirements Level)")
    print("   Mode: Level Extraction (No Full Table)")
    
    if not os.path.exists(OUTPUT_FILE):
        print(f"ERROR: {OUTPUT_FILE} not found!")
        return
        
    print(f"Loading {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    print(f"Found {len(data)} opportunities to process.")
    
    results = {
        'processed': 0, 'errors': 0, 'total': len(data), 'lock': threading.Lock()
    }
    
    enriched_data = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = []
        for item in data:
            futures.append(executor.submit(process_permit_enrichment, item, results))
            
        for future in concurrent.futures.as_completed(futures):
            try:
                enriched_data.append(future.result())
            except Exception as e:
                logger.error(f"Thread error: {e}")
                
    def get_sort_date(item):
        if not item.get('history'): return datetime.min
        latest_date = datetime.min
        for event in item['history']:
            date_str = event.get('event_date')
            if date_str:
                try:
                    dt = datetime.strptime(date_str, '%d/%m/%Y')
                    if dt > latest_date: latest_date = dt
                except: pass
        return latest_date

    enriched_data.sort(key=get_sort_date, reverse=True)
    
    print(f"Saving {len(enriched_data)} enriched permits to {OUTPUT_FILE}...")
    save_json(enriched_data, OUTPUT_FILE)
    print("DONE.")

if __name__ == "__main__":
    main()
