"""
Script to reprocess specific skipped permits and add them to opportunities.json without filtering.
Based on analyze_permits.py.
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
from openai import OpenAI
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
INPUT_FILE = "add_skipped_permits.txt"
OUTPUT_FILE = "opportunities.json"
OUTPUT_FILE_JSONL = "opportunities.jsonl"
DEBUG_REQUESTS_FILE = "model_requests_reprocess.txt"
RELEVANT_FILE = "relevant_permits.txt" # We will append here too to keep state consistent

# LLM System Prompt - FORCED RELEVANCE
SYSTEM_PROMPT = """You are a real estate investment analyst specializing in Israeli construction permits.

You will receive the "מהות הבקשה" (Request Intention) text from a Bat Yam building permit. 
The user has identified this permit as a RELEVANT investment opportunity.

Your task is to analyze the text and extract the project details. 
You MUST set "is_relevant" to true.

OUTPUT FORMAT (JSON only, no markdown, no code blocks):
{
  "is_relevant": true,
  "permit_id": "...",
  "project_type": "Type of project (e.g., New Construction, Addition, Renovation)",
  "description": "Copy the Hebrew description text",
  "num_units": "number of residential units if mentioned (יח\"ד), otherwise null",
  "key_features": ["list", "of", "key", "features"]
}
"""

# Locks
opportunities_lock = threading.Lock()
relevant_lock = threading.Lock()
log_lock = threading.Lock()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# HELPER FUNCTIONS (Copied from analyze_permits.py)
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

def flip_text(text: str) -> str:
    if not text: return text
    if any("\u0590" <= char <= "\u05EA" for char in text):
        return text[::-1]
    return text

def _get_text(el) -> Optional[str]:
    if not el: return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def _has_meetings(soup: BeautifulSoup) -> bool:
    btn_meetings = soup.find('div', id='btn-meetings')
    if not btn_meetings: return False
    count_span = btn_meetings.find('span', class_='spn')
    if count_span:
        match = re.search(r'\((\d+)\)', count_span.get_text(strip=True))
        if match: return int(match.group(1)) > 0
    return False

def _parse_meetings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    meetings = []
    table_div = soup.find('div', id='table-meetings')
    if not table_div: return []
    main_table = table_div.find('table')
    if not main_table: return []
    tbody = main_table.find('tbody')
    if not tbody: return []
    all_rows = tbody.find_all('tr', recursive=False)
    i = 0
    while i < len(all_rows):
        row = all_rows[i]
        classes = row.get('class', [])
        if 'accordion-toggle' in classes:
            cols = row.find_all('td', recursive=False)
            meeting_id = None
            meeting_date = None
            meeting_url = None
            
            meeting_link = row.find('a', href=lambda x: x and 'getMeeting' in str(x))
            if meeting_link:
                meeting_id = _get_text(meeting_link)
                match = re.search(r'getMeeting\((\d+),(\d+)\)', meeting_link.get('href', ''))
                if match:
                    meeting_url = f"https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetVaadaFile&siteid=81&t={match.group(1)}&v={match.group(2)}&arguments=siteid,t,v"
            
            if not meeting_id:
                for col in cols:
                    text = _get_text(col)
                    if text and re.match(r'^\d{8,}$', text.strip()):
                        meeting_id = text.strip()
                        break
            
            for col in cols:
                text = _get_text(col)
                if text and re.match(r'^\d{2}/\d{2}/\d{4}$', text.strip()):
                    meeting_date = text.strip()
                    break
            
            essence = None
            j = i + 1
            while j < len(all_rows):
                next_row = all_rows[j]
                if 'accordion-toggle' in next_row.get('class', []): break
                hidden_td = next_row.find('td', class_='hiddenRow')
                if hidden_td or 'hiddenRow' in next_row.get('class', []):
                    details_div = next_row.find('div', class_=lambda x: x and 'accordion-body' in str(x).lower())
                    if details_div:
                        for table in details_div.find_all('table'):
                            th = table.find('th')
                            if th and 'מהות' in _get_text(th):
                                tbody_inner = table.find('tbody')
                                if tbody_inner and tbody_inner.find('td'):
                                    essence = _get_text(tbody_inner.find('td'))
                    break
                j += 1
            
            if meeting_id:
                meetings.append({
                    'meeting_id': meeting_id,
                    'meeting_date': meeting_date,
                    'meeting_url': meeting_url,
                    'essence': essence,
                    'decision_status': None
                })
        i += 1
    return meetings

def _parse_request_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    info_table = soup.select_one("#info-main table tbody")
    if not info_table: return {"request_type": None, "main_use": None, "request_description": None}
    rows = info_table.select("tr")
    request_type = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    main_use = _get_text(rows[3].find_all("td")[1]) if len(rows) >= 4 and len(rows[3].find_all("td")) > 1 else None
    request_description = _get_text(rows[4].find_all("td")[1]) if len(rows) >= 5 and len(rows[4].find_all("td")) > 1 else None
    return {"request_type": request_type, "main_use": main_use, "request_description": request_description}

def _parse_address(soup: BeautifulSoup) -> Optional[str]:
    navbar = soup.select_one("#navbar-titles-id")
    if navbar:
        h5_elements = navbar.find_all("h5")
        if len(h5_elements) >= 4:
            return _get_text(h5_elements[3])
    address = soup.select_one("#navbar-titles-id .col-md-4 h5")
    return _get_text(address)

def _parse_applicants(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    table = soup.select_one("#table-baaley-inyan table tbody")
    if not table: return {"requestor": None, "owner": None, "author": None}
    rows = table.select("tr")
    requestor = _get_text(rows[0].find_all("td")[1]) if len(rows) >= 1 and len(rows[0].find_all("td")) > 1 else None
    owner = _get_text(rows[1].find_all("td")[1]) if len(rows) >= 2 and len(rows[1].find_all("td")) > 1 else None
    author = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    return {"requestor": requestor, "owner": owner, "author": author}

def _parse_parcels(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    parcels = []
    table = soup.select_one("#table-gushim-helkot table tbody")
    if not table: return parcels
    for row in table.select("tr"):
        tds = row.find_all("td")
        if len(tds) >= 3:
            parcels.append({"gush": _get_text(tds[1]), "helka": _get_text(tds[2])})
    return parcels

def _parse_history(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    history = []
    table = soup.select_one("#table-events table tbody")
    if not table: return history
    for row in table.select("tr"):
        tds = row.find_all("td")
        if not tds: continue
        history.append({
            "event_type": _get_text(tds[0]) if len(tds) > 0 else None,
            "event_description": _get_text(tds[1]) if len(tds) > 1 else None,
            "event_date": _get_text(tds[2]) if len(tds) > 2 else None,
            "event_end_date": _get_text(tds[3]) if len(tds) > 3 else None,
        })
    return history

def fetch_permit_data(permit_id: str, max_retries: int = 2) -> Tuple[Optional[str], Dict[str, Any]]:
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=session_id)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, proxies=proxies, verify=VERIFY_SSL)
            if response.status_code == 429:
                time.sleep(40 * (attempt + 1))
                continue
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            soup = BeautifulSoup(response.text, 'html.parser')
            
            mahut_div = soup.find('div', id='mahut')
            if mahut_div:
                text = mahut_div.get_text(separator=' ', strip=True).replace('מהות הבקשה', '', 1).strip()
                mahut_text = text.replace('\u200f', '').replace('\u200e', '').strip()
            else:
                if attempt < max_retries:
                    time.sleep(40)
                    continue
                return None, {}
            
            metadata = {
                "request_type": _parse_request_info(soup).get("request_type"),
                "main_use": _parse_request_info(soup).get("main_use"),
                "request_description": _parse_request_info(soup).get("request_description"),
                "address": _parse_address(soup),
                "applicants": _parse_applicants(soup),
                "parcels": _parse_parcels(soup),
                "history": _parse_history(soup),
                "meeting_history": _parse_meetings(soup) if _has_meetings(soup) else [],
            }
            return mahut_text, metadata
            
        except Exception:
            time.sleep(5)
            continue
    return None, {}

def analyze_with_ai(mahut_text: str, permit_id: str, client: OpenAI, max_retries: int = 3) -> Optional[dict]:
    for attempt in range(max_retries):
        try:
            user_content = f"Permit ID: {permit_id}\n\nמהות הבקשה:\n{mahut_text}"
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            response_text = (response.choices[0].message.content or "").strip()
            if not response_text:
                time.sleep(2)
                continue
                
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
                
            result = json.loads(response_text)
            result['permit_id'] = permit_id
            return result
        except Exception:
            time.sleep(2)
            continue
    return None

def save_opportunity_incremental(opportunity: Dict[str, Any], output_file_jsonl: str):
    try:
        json_line = json.dumps(opportunity, ensure_ascii=False) + '\n'
        with opportunities_lock:
            with open(output_file_jsonl, 'a', encoding='utf-8') as f:
                f.write(json_line)
    except Exception as e:
        logger.error(f"Failed to save {opportunity.get('permit_id')} to JSONL: {e}")

def convert_jsonl_to_json(jsonl_file: str, json_file: str):
    print(f"\nConverting {jsonl_file} to {json_file}...")
    new_items = []
    if os.path.exists(jsonl_file):
        with open(jsonl_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    try:
                        new_items.append(json.loads(line))
                    except: pass
    
    existing_items = []
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_items = json.load(f)
        except: pass
        
    combined_map = {item.get('permit_id'): item for item in existing_items}
    for item in new_items:
        combined_map[item.get('permit_id')] = item
        
    final_list = list(combined_map.values())
    
    # Sort
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
        
    final_list.sort(key=get_sort_date, reverse=True)
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(final_list, f, ensure_ascii=False, indent=2)
    
    print(f"   ✅ Saved {len(final_list)} total opportunities to {json_file}")
    
    # Cleanup
    if os.path.exists(jsonl_file):
        try:
            os.remove(jsonl_file)
        except: pass

def process_permit(permit_id: str, client: OpenAI, results: Dict[str, int]) -> None:
    try:
        mahut_text, metadata = fetch_permit_data(permit_id)
        if not mahut_text:
            with results['lock']: results['errors'] += 1
            print(f"❌ [{permit_id}] Failed to fetch info")
            return

        result = analyze_with_ai(mahut_text, permit_id, client)
        if result is None:
            with results['lock']: results['errors'] += 1
            print(f"❌ [{permit_id}] Failed AI analysis")
            return

        # FORCE SAVE regardless of is_relevant (prompt should ensure it's true anyway)
        enriched = {**result, **metadata}
        enriched['is_relevant'] = True # Ensure it's true
        
        save_opportunity_incremental(enriched, OUTPUT_FILE_JSONL)
        
        with results['lock']:
            results['relevant'] += 1
            results['processed'] += 1
        
        project_type = result.get('project_type', 'Unknown')
        print(f"✅ [{permit_id}] ADDED: {flip_text(project_type)}")

    except Exception as e:
        logger.error(f"Error {permit_id}: {e}")
        with results['lock']: results['errors'] += 1

def main():
    print("🚀 Starting Reprocess Skipped Permits Script")
    
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("ERROR: Missing OPENAI_API_KEY")
        return
    client = OpenAI(api_key=api_key)
    
    if not os.path.exists(INPUT_FILE):
        print(f"ERROR: {INPUT_FILE} not found")
        return
        
    with open(INPUT_FILE, 'r') as f:
        permit_ids = [line.strip() for line in f if line.strip()]
        
    print(f"Found {len(permit_ids)} permits to process.")
    
    results = {
        'processed': 0, 'relevant': 0, 'errors': 0, 'total': len(permit_ids), 'lock': threading.Lock()
    }
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(process_permit, pid, client, results) for pid in permit_ids]
        concurrent.futures.wait(futures)
        
    convert_jsonl_to_json(OUTPUT_FILE_JSONL, OUTPUT_FILE)
    print("DONE.")

if __name__ == "__main__":
    main()
