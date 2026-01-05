import csv
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse
from io import StringIO
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
import os
import random
import string
import threading
import concurrent.futures
from dotenv import load_dotenv
import urllib3
from datetime import datetime

# Suppress SSL warnings since verify=False is often needed for proxies
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ============================================================================
# ⚙️ CONFIGURATION & ENVIRONMENT SETUP
# ============================================================================

USE_PROXY = True  # שנה ל-False אם אתה רוצה לעבוד בלי פרוקסי

# טעינת משתני סביבה מקובץ .env או .env.example שנמצא שתי תיקיות למעלה (שורש הפרויקט)
# This logic navigates 2 folders up to find the project root
base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
env_path = os.path.join(base_path, '.env')
env_example_path = os.path.join(base_path, '.env.example')

print(f"🔧 Configuration search path: {base_path}")

# Try .env first, then fallback to .env.example
if os.path.exists(env_path):
    load_dotenv(dotenv_path=env_path)
    print(f"✅ Loaded environment from: {env_path}")
elif os.path.exists(env_example_path):
    load_dotenv(dotenv_path=env_example_path)
    print(f"⚠️  Loaded environment from EXAMPLE file: {env_example_path}")
else:
    print("⚠️  No .env file found. Relying on system environment variables.")

# פרטי הפרוקסי (קבל אותם מהדשבורד של Bright Data / הספק שלך)
# UPDATED: Changed default to zproxy.lum-superproxy.io which often works better for specific targets
PROXY_HOST = os.getenv("PROXY_HOST", "zproxy.lum-superproxy.io")
PROXY_PORT = os.getenv("PROXY_PORT", "22225")  # Default Bright Data residential port

# טעינת שם המשתמש והסיסמה משתני הסביבה
# For Bright Data, username format is usually: brd-customer-{customer_id}-zone-{zone_name}
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

# SSL Verification setting
VERIFY_SSL = False

# WORKER CONFIGURATION
MAX_WORKERS = 7

# ============================================================================
# END OF CONFIGURATION
# ============================================================================

# ============================================================================
# THREAD SAFETY LOCKS
# ============================================================================
output_lock = threading.Lock()

# ============================================================================
# HELPER FUNCTIONS
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

def clean_text(text):
    if isinstance(text, str):
        return text.strip().replace('\xa0', ' ')
    return text

def extract_mavat_link(onclick_text):
    if not onclick_text:
        return None
    match = re.search(r"encodeURI\('(.*?)'\)", onclick_text)
    if match:
        return match.group(1)
    
    match_url = re.search(r"(https://mavat\.iplan\.gov\.il/[^\']+)", onclick_text)
    if match_url:
        return match_url.group(1)
        
    return None

def detect_captcha(response):
    """Detect if the response contains a CAPTCHA challenge."""
    if not response:
        return False
    
    if response.status_code in [403, 429]:
        return True
    
    if len(response.content) < 500:
        return True
    
    content_lower = response.text.lower()
    captcha_keywords = ['captcha', 'robot', 'verification', 'recaptcha', 'challenge']
    
    for keyword in captcha_keywords:
        if keyword in content_lower:
            return True
    
    return False

def scrape_plan(serial_id, taba_number, max_retries=3, max_captcha_retries=3):
    url = f"https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetTabaFile&siteid=81&n={serial_id}&arguments=siteid,n"
    
    # Generate a random session ID for proxy rotation
    session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
    proxies = get_proxy_dict(session_id=session_id)
    
    # SENIOR TIP: Optimized headers
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br', 
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    response = None
    captcha_retry_count = 0
    
    # print(f"  📡 Requesting ID {serial_id}...")
    
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(
                url, 
                headers=headers,
                timeout=20,
                proxies=proxies,
                verify=VERIFY_SSL
            )
            
            # Handle 502 Bad Gateway (common with proxies)
            if response.status_code == 502:
                # print(f"     ⚠️  502 Proxy Gateway Error - Retrying...")
                time.sleep(2)
                continue
            
            response.raise_for_status()
            
            # Check for CAPTCHA
            if detect_captcha(response):
                captcha_retry_count += 1
                if captcha_retry_count <= max_captcha_retries:
                    wait_time = random.randint(30, 40)
                    print(f"     ⚠️  CAPTCHA detected for {taba_number}! Waiting {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    print(f"     ❌ CAPTCHA block persistent for {taba_number}. Skipping.")
                    return None
            
            # Success
            break
            
        except Exception as e:
            # print(f"     ❌ Error for {taba_number} (Attempt {attempt}): {str(e)[:100]}")
            if attempt < max_retries:
                time.sleep(3)
            else:
                return None

    if not response:
        return None
    
    # Parsing logic starts here
    soup = BeautifulSoup(response.content, 'html.parser')
    
    plan_data = {
        "plan_number": taba_number,
        "plan_type": None,
        "plan_name": None,
        "general_info": {},
        "history": [],
        "meeting_history": []
    }

    # --- 1. חילוץ כותרות ---
    type_label = soup.find('div', string=re.compile('סוג התוכנית:'))
    if type_label:
        type_val_div = type_label.find_next('div', class_='top-navbar-info-desc')
        if type_val_div:
            plan_data["plan_type"] = clean_text(type_val_div.get_text())

    name_label = soup.find('div', string=re.compile('שם התוכנית:'))
    if name_label:
        name_val_div = name_label.find_next('div', class_='top-navbar-info-desc')
        if name_val_div:
            plan_data["plan_name"] = clean_text(name_val_div.get_text())

    # --- 2. חילוץ מידע כללי ---
    try:
        dfs = pd.read_html(StringIO(str(soup)))
        field_mapping = {
            "סטטוס תוכנית": "status",
            "תאריך הסטטוס": "status_date",
            "בסמכות": "authority",
            "שכונה": "neighborhood",
            "שטח": "area",
            "יזם": "developer",
            'קישור למבא"ת': "mavat_link"
        }
        for df in dfs:
            table_str = df.to_string()
            if "סטטוס תוכנית" in table_str or "תאריך הסטטוס" in table_str:
                df = df.dropna(how='all')
                for index, row in df.iterrows():
                    if len(row) < 2: continue
                    key = clean_text(str(row.iloc[0]))
                    value = clean_text(str(row.iloc[1]))
                    for hebrew_key, english_key in field_mapping.items():
                        if hebrew_key in key:
                            plan_data["general_info"][english_key] = value
                break
    except ValueError:
        pass

    # Mavat link fix
    mavat_td = soup.find('td', string=re.compile('קישור למבא"ת'))
    if mavat_td:
        link_td = mavat_td.find_next_sibling('td')
        if link_td:
            anchor = link_td.find('a')
            if anchor and anchor.has_attr('onclick'):
                plan_data["general_info"]["mavat_link"] = extract_mavat_link(anchor['onclick'])

    # --- 3. חילוץ היסטוריה ---
    history_div = soup.find(id="table-shlavim")
    if history_div:
        try:
            hist_dfs = pd.read_html(StringIO(str(history_div)))
            if hist_dfs:
                hist_df = hist_dfs[0]
                if len(hist_df.columns) >= 2:
                    hist_df = hist_df.iloc[:, [0, 1]] 
                    hist_df.columns = ["date", "stage"]
                    records = hist_df.to_dict('records')
                    for rec in records:
                        d = clean_text(str(rec['date']))
                        s = clean_text(str(rec['stage']))
                        if d and s and "תאריך" not in d: 
                             plan_data["history"].append([d, s])
        except ValueError:
            pass

    # --- 4. Parse committee meetings ---
    try:
        plan_data["meeting_history"] = _parse_plan_meetings(soup)
    except Exception as e:
        print(f"     ⚠️  Meetings parse error: {e}")
        plan_data["meeting_history"] = []

    # Summary log
    # info_count = len(plan_data['general_info'])
    # hist_count = len(plan_data['history'])
    # meet_count = len(plan_data['meeting_history'])
    # print(f"     ✓ Extracted: Info({info_count}), History({hist_count}), Meetings({meet_count})")
    
    return plan_data

def _get_text(el) -> Optional[str]:
    if not el: return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def _parse_plan_meetings(soup: BeautifulSoup) -> List[Dict[str, Any]]:
    meetings = []
    table_div = soup.find('div', id='table-meetings')
    if not table_div: return []
    
    main_table = table_div.find('table')
    if not main_table: return []
    
    thead = main_table.find('thead')
    if not thead: return []
    
    headers = thead.find_all('th')
    column_map = {}
    for idx, th in enumerate(headers):
        header_text = _get_text(th)
        if not header_text: continue
        if 'שם הועדה' in header_text: column_map['meeting_type'] = idx
        elif 'מספר' in header_text and 'ישיבה' in header_text: column_map['meeting_number'] = idx
        elif 'תאריך' in header_text and 'ישיבה' in header_text: column_map['meeting_date'] = idx
        elif 'יום' in header_text: column_map['day_of_week'] = idx
        elif 'שעה' in header_text: column_map['meeting_time'] = idx
    
    tbody = main_table.find('tbody')
    if not tbody: return []
    
    all_rows = tbody.find_all('tr', recursive=False)
    for row in all_rows:
        if 'accordion-toggle' in row.get('class', []):
            cols = row.find_all('td', recursive=False)
            
            m_type = _get_text(cols[column_map['meeting_type']]) if 'meeting_type' in column_map and len(cols) > column_map['meeting_type'] else None
            m_num_text = _get_text(cols[column_map['meeting_number']]) if 'meeting_number' in column_map and len(cols) > column_map['meeting_number'] else None
            m_date = _get_text(cols[column_map['meeting_date']]) if 'meeting_date' in column_map and len(cols) > column_map['meeting_date'] else None
            m_day = _get_text(cols[column_map['day_of_week']]) if 'day_of_week' in column_map and len(cols) > column_map['day_of_week'] else None
            m_time = _get_text(cols[column_map['meeting_time']]) if 'meeting_time' in column_map and len(cols) > column_map['meeting_time'] else None
            
            m_link = None
            if 'meeting_number' in column_map and len(cols) > column_map['meeting_number']:
                td_num = cols[column_map['meeting_number']]
                a_tag = td_num.find('a')
                if a_tag and a_tag.has_attr('href'):
                    href_val = a_tag['href']
                    match = re.search(r"getMeeting\s*\(\s*(\d+)\s*,\s*(\d+)\s*\)", href_val)
                    if match:
                        arg1, arg2 = match.groups()
                        m_link = f"https://batyam.complot.co.il/binyan/#meeting/{arg1}/{arg2}"
                    else:
                        m_link = href_val
            
            meeting_data = {
                'meeting_type': m_type,
                'meeting_number': m_num_text,
                'meeting_date': m_date,
                'day_of_week': m_day,
                'meeting_time': m_time,
                'meeting_link': m_link 
            }
            if meeting_data['meeting_number'] or meeting_data['meeting_date']:
                meetings.append(meeting_data)
    return meetings

def load_existing_plans(output_json):
    scraped_plans = set()
    existing_data = []
    
    # Check JSON file
    if os.path.exists(output_json):
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    for plan in existing_data:
                        if isinstance(plan, dict) and 'plan_number' in plan:
                            scraped_plans.add(str(plan['plan_number']))
            print(f"Found {len(scraped_plans)} already scraped plans in JSON.")
        except: pass
        
    return scraped_plans, existing_data

def format_json_compact_history(data):
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    def compress_array_field(json_string, field_name):
        pattern = r'(\s+)"' + field_name + r'":\s*\['
        matches = list(re.finditer(pattern, json_string))
        for match in reversed(matches):
            depth, i = 0, match.end() - 1
            start_pos = i
            end_pos = -1
            while i < len(json_string):
                if json_string[i] == '[': depth += 1
                elif json_string[i] == ']':
                    depth -= 1
                    if depth == 0:
                        end_pos = i
                        break
                i += 1
            if end_pos != -1:
                indent = match.group(1)
                content = json_string[start_pos + 1:end_pos]
                compressed = re.sub(r'\s+', ' ', content).strip()
                compressed = re.sub(r'\s*\[\s*', '[', compressed)
                compressed = re.sub(r'\s*\]\s*', ']', compressed)
                compressed = re.sub(r'\s*,\s*', ', ', compressed)
                json_string = json_string[:match.start()] + f'{indent}"{field_name}": [{compressed}]' + json_string[end_pos + 1:]
        return json_string
    json_str = compress_array_field(json_str, "history")
    json_str = compress_array_field(json_str, "meeting_history")
    return json_str

def save_plan_incremental_jsonl(plan_data: Dict[str, Any], output_file_jsonl: str):
    """
    Save a single plan to JSONL file immediately.
    """
    try:
        json_line = json.dumps(plan_data, ensure_ascii=False) + '\n'
        with output_lock:
            with open(output_file_jsonl, 'a', encoding='utf-8') as f:
                f.write(json_line)
    except Exception as e:
        print(f"Failed to save plan {plan_data.get('plan_number')} to JSONL: {e}")

def convert_jsonl_to_json(input_jsonl: str, output_json: str, existing_data: list = None):
    """
    Convert JSONL file to JSON, merging with existing data.
    """
    all_data = existing_data[:] if existing_data else []
    
    # Check if JSONL exists
    if os.path.exists(input_jsonl):
        print(f"Reading temporary data from {input_jsonl}...")
        try:
            with open(input_jsonl, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            data = json.loads(line)
                            all_data.append(data)
                        except json.JSONDecodeError:
                            pass
        except Exception as e:
            print(f"Error reading JSONL: {e}")
            
    # Remove duplicates based on plan_number, keeping the latest one
    # (assuming later in the list = newer or same)
    unique_map = {}
    for item in all_data:
        if 'plan_number' in item:
            unique_map[str(item['plan_number'])] = item
            
    final_list = list(unique_map.values())
    
    print(f"Saving {len(final_list)} total plans to {output_json}...")
    try:
        formatted_json = format_json_compact_history(final_list)
        with open(output_json, 'w', encoding='utf-8') as f:
            f.write(formatted_json)
        # Optional: Remove JSONL after successful save? 
        # For safety/debugging, we might keep it or rename it. 
        # But per standard practice in previous file, we leave it or overwrite next time.
        # Here we will just leave it.
    except Exception as e:
        print(f"Error saving final JSON: {e}")

def process_plan(row, output_jsonl):
    """
    Worker function to process a single plan.
    """
    taba_number = row['Taba_Number']
    serial_id = row['Serial_ID']
    
    # print(f"Scraping {taba_number}...")
    data = scrape_plan(serial_id, taba_number)
    
    if data:
        # Add success status if not present
        if 'status' not in data:
            data['status'] = 'success'
        save_plan_incremental_jsonl(data, output_jsonl)
        print(f"✅ Saved {taba_number}")
        return True
    else:
        print(f"❌ Failed to scrape {taba_number}. Saving failure record.")
        failed_record = {
            "plan_number": taba_number,
            "status": "failed",
            "last_attempt": datetime.now().isoformat()
        }
        save_plan_incremental_jsonl(failed_record, output_jsonl)
        return False

def main():
    input_csv = 'bat_yam_taba_list.csv'
    
    # <--- שינוי 2: שם קובץ דינמי לפי התאריך של היום
    today_str = datetime.now().strftime('%Y_%m_%d')
    output_json = f'bat_yam_plans_data_{today_str}.json'
    output_jsonl = f'bat_yam_plans_data_{today_str}.jsonl'
    
    print("=" * 60)
    print("🚀 Starting Bat Yam TABA Scraper (Parallel Version)")
    print(f"📅 Daily Output File: {output_json}")
    print(f"⚡ Workers: {MAX_WORKERS}")
    print("=" * 60)
    print(f"Proxy Configured: {USE_PROXY}")
    
    if USE_PROXY:
        if not test_proxy_connection():
            print("\n❌ Proxy Connection FAILED.")
            print("   Please check your .env file credentials.")
            print("   Continuing without proxy might result in blocking...\n")
            # uncomment next line to stop on error
            # return 
    
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print(f"Error: CSV file '{input_csv}' not found.")
        return

    # Load from JSON to know what to skip (if restart)
    scraped_plans, existing_data = load_existing_plans(output_json)
    
    # Also load from JSONL if exists (crash recovery)
    if os.path.exists(output_jsonl):
        try:
            with open(output_jsonl, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.strip():
                        try:
                            j = json.loads(line)
                            if 'plan_number' in j:
                                scraped_plans.add(str(j['plan_number']))
                        except: pass
            print(f"Found additional plans in JSONL. Total unique processed: {len(scraped_plans)}")
        except: pass

    df_to_scrape = df[~df['Taba_Number'].astype(str).isin(scraped_plans)].copy()
    
    remaining = len(df_to_scrape)
    if remaining == 0:
        print("✅ All plans already scraped.")
        # Ensure JSON is up to date with JSONL content if any
        convert_jsonl_to_json(output_jsonl, output_json, existing_data)
        return
    
    print(f"Plans to scrape: {remaining}")
    
    # Convert DataFrame rows to list of dicts for safe iteration
    rows_to_process = [row for _, row in df_to_scrape.iterrows()]
    
    start_time = time.time()
    
    try:
        # Parallel Execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [
                executor.submit(process_plan, row, output_jsonl)
                for row in rows_to_process
            ]
            concurrent.futures.wait(futures)
            
        duration = time.time() - start_time
        print(f"\nProcessing completed in {duration:.2f} seconds.")
        
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user. Saving progress...")
        
    finally:
        # Final conversion
        convert_jsonl_to_json(output_jsonl, output_json, existing_data)
        
        # Cleanup JSONL file
        if os.path.exists(output_jsonl):
            try:
                os.remove(output_jsonl)
                print(f"🗑️ Cleaned up temporary file: {output_jsonl}")
            except Exception as e:
                print(f"⚠️ Could not delete {output_jsonl}: {e}")
        
        print("\n✅ Done!")

if __name__ == "__main__":
    main()