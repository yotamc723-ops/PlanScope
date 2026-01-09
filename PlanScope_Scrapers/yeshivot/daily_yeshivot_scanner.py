import os
import sys
import json
import time
import shutil
import glob
import random
import string
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv

# Selenium & Webdriver Manager
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_MANAGER = True
except Exception:
    HAS_MANAGER = False

# --- Configuration ---
CURRENT_DIR = Path(__file__).parent
# Path goes 3 levels up: yeshivot/ -> PlanScope_Scrapers/ -> PlanScope/
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

PROXY_HOST = os.getenv("PROXY_HOST")
PROXY_PORT = os.getenv("PROXY_PORT")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")
USE_PROXY = os.getenv("USE_PROXY", "False").lower() == "true"

# Import Analyzer after environment is loaded
import pdf_analyzer

LAST_MEETING_FILE = CURRENT_DIR / "last_meeting.json"
PDF_DIR = CURRENT_DIR / "decision_protocols"
PROCESSED_JSON_DIR = CURRENT_DIR / "processed_json"
ALL_MEETINGS_FILE = PROCESSED_JSON_DIR / "all_meetings_data.json"

# --- Proxy Helper ---
def get_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass):
    extension_dir = os.path.join(os.getcwd(), "proxy_auth_ext")
    if not os.path.exists(extension_dir):
        os.makedirs(extension_dir)

    manifest_json = """
    {
        "version": "1.0.0",
        "manifest_version": 2,
        "name": "Chrome Proxy",
        "permissions": [
            "proxy",
            "tabs",
            "unlimitedStorage",
            "storage",
            "<all_urls>",
            "webRequest",
            "webRequestBlocking"
        ],
        "background": {
            "scripts": ["background.js"]
        },
        "minimum_chrome_version": "22.0.0"
    }
    """

    background_js = f"""
    var config = {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: "{proxy_host}",
                port: parseInt({proxy_port})
            }},
            bypassList: ["localhost", "127.0.0.1"]
        }}
    }};

    chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

    function callbackFn(details) {{
        return {{
            authCredentials: {{
                username: "{proxy_user}",
                password: "{proxy_pass}"
            }}
        }};
    }}

    chrome.webRequest.onAuthRequired.addListener(
            callbackFn,
            {{urls: ["<all_urls>"]}},
            ['blocking']
    );
    """

    manifest_file = os.path.join(extension_dir, "manifest.json")
    with open(manifest_file, "w") as f:
        f.write(manifest_json)

    background_file = os.path.join(extension_dir, "background.js")
    with open(background_file, "w") as f:
        f.write(background_js)

    zip_file = os.path.join(os.getcwd(), "proxy_auth_plugin.zip")
    with zipfile.ZipFile(zip_file, 'w') as zp:
        zp.write(manifest_file, "manifest.json")
        zp.write(background_file, "background.js")
    
    # Cleanup directory
    shutil.rmtree(extension_dir)
    
    return zip_file

# --- State Management ---
def load_last_meeting_state():
    if LAST_MEETING_FILE.exists():
        try:
            with open(LAST_MEETING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_last_meeting_state(meeting_number, date):
    with open(LAST_MEETING_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            "last_meeting_number": meeting_number,
            "last_meeting_date": date,
            "updated_at": datetime.now().isoformat()
        }, f, indent=4)

def wait_for_download(download_dir, existing_files, timeout=60):
    """
    Waits for a NEW file to appear in the directory (not in existing_files).
    Returns the path to the new file.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - existing_files
        
        # Filter temp/downloading files
        valid_new_files = [
            f for f in new_files 
            if not f.endswith(".crdownload") and not f.endswith(".tmp") and not f.startswith(".")
        ]
        
        if valid_new_files:
            # Found a specific new file
            return os.path.join(download_dir, valid_new_files[0])
            
        time.sleep(1)
    return None

from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# --- Helper: Download Logic (UI Interaction) ---
def download_meeting_protocols_via_ui(driver, meeting_number, meeting_date, output_dir):
    """
    Downloads 'Protocol of Decisions' for a specific meeting by interacting with the UI:
    1. Finds the row for the meeting number.
    2. Clicks the 'Document Archive' button (col 8).
    3. Selects the protocol link from the modal.
    4. Downloads and closes modal.
    5. Renames file to {meeting_number}_{date}.pdf
    """
    downloaded_files = []
    print(f"   -> Interacting with UI for Meeting {meeting_number}...")
    
    try:
        # 1. Find the specific row for this meeting (Table is already visible)
        # Using XPath to find the row where the link text equals meeting_number
        row_xpath = f"//a[normalize-space(text())='{meeting_number}']/ancestor::tr"
        row = driver.find_element(By.XPATH, row_xpath)
        
        # 2. Click 'Document Archive' button (8th column -> button)
        archive_btn = row.find_element(By.XPATH, "./td[8]/button")
        
        # Scroll to button to ensure visibility
        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", archive_btn)
        time.sleep(1)
        
        # JS Click is often safer for buttons in tables
        driver.execute_script("arguments[0].click();", archive_btn)
        print("      Clicked archive button.")
        
        # 3. Wait for Modal and Find Link
        wait = WebDriverWait(driver, 10)
        
        # VERIFICATION: Check Modal Header
        # More robust: Get element by class and check text in Python
        try:
            # Wait for modal header to be visible
            wait.until(EC.visibility_of_element_located((By.CLASS_NAME, "modal-header")))
            
            # Get all visible headers (should be one)
            headers = driver.find_elements(By.CLASS_NAME, "modal-header")
            header_text = ""
            verified = False
            
            for h in headers:
                if h.is_displayed():
                    header_text = h.text
                    if str(meeting_number) in header_text:
                        verified = True
                        break
            
            if verified:
                print(f"      Verified Modal Header for {meeting_number}.")
            else:
                 print(f"      CRITICAL: Modal header verification failed. Expected {meeting_number} in '{header_text}'.")
                 ActionChains(driver).send_keys(Keys.ESCAPE).perform()
                 return []
                 
        except Exception as e:
             print(f"      Error during modal verification: {e}")
             ActionChains(driver).send_keys(Keys.ESCAPE).perform()
             return []

        # Wait for modal content or the specific link
        protocol_link_xpath = "//a[contains(text(), 'פרוטוקול החלטות')]"
        try:
            protocol_link = wait.until(EC.element_to_be_clickable((By.XPATH, protocol_link_xpath)))
            print("      Found 'Protocol of Decisions' link.")
            
            # Capture real URL
            pdf_url = protocol_link.get_attribute("href")
            print(f"      PDF URL Found: {pdf_url}")
            
            # Direct Download via Requests (More robust than Selenium headless download)
            # Sanitize date (replace / with -)
            safe_date = meeting_date.replace('/', '-')
            new_filename = f"{meeting_number}_{safe_date}.pdf"
            new_filepath = os.path.join(output_dir, new_filename)
            
            # Check overwrite
            if os.path.exists(new_filepath):
                os.remove(new_filepath)
                
            try:
                print(f"      Downloading via requests...")
                response = requests.get(pdf_url, stream=True, timeout=30)
                response.raise_for_status()
                
                with open(new_filepath, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                        
                print(f"      Downloaded & Saved: {new_filename}")
                downloaded_files.append({
                    "filename": new_filename,
                    "pdf_url": pdf_url
                })
                
            except Exception as e:
                print(f"      Download Error (requests): {e}")

        except Exception as e:
            print(f"      'Protocol of Decisions' link not found or interaction error: {e}")
            
        # 4. Close Modal (Press Escape)
        print("      Closing modal...")
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(1) # Wait for animation
            
    except Exception as e:
        print(f"      Error interacting with UI for {meeting_number}: {e}")
        # Try to close modal just in case we are stuck
        try:
            ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        except:
            pass
        
    return downloaded_files

# --- Main Logic ---
def run_daily_scan():
    print("Starting Daily Yeshivot Scanner...")
    
    # 1. Setup Driver
    chrome_options = Options()
    # chrome_options.add_argument("--headless") # Commented out for debugging if needed, but per plan keeps headless. 
    # Use headless for server/background run
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    # PDF Download prefs
    prefs = {
        "download.default_directory": str(PDF_DIR.absolute()),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    # Must also set CDP for headless download to work reliably in some versions
    # We do this after driver creation

    proxy_plugin = None
    if USE_PROXY and PROXY_USER and PROXY_PASS:
        print("Using Proxy...")
        proxy_plugin = get_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        chrome_options.add_extension(proxy_plugin)
    
    driver = None
    
    try:
        if HAS_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            
        # CDP Command for Headless Download
        driver.execute_cdp_cmd("Page.setDownloadBehavior", {
            "behavior": "allow",
            "downloadPath": str(PDF_DIR.absolute())
        })
            
        wait = WebDriverWait(driver, 60)

        # 2. Construct Query URL
        # We look back 30 days and forward 30 days to cover recent past and near future meetings
        today = datetime.now()
        start_date = (today - timedelta(days=60)).strftime("%d/%m/%Y") # Extended check 
        end_date = (today + timedelta(days=60)).strftime("%d/%m/%Y")   # Extended check
        
        base_url = "https://batyam.complot.co.il/yeshivot/#search/GetMeetingByDate"
        # dynamic params
        # IMPORTANT: matches format in yeshivot_scraper.py including &arguments param
        target_url = f"{base_url}&siteid=81&v=0&fd={start_date}&td={end_date}&l=true&arguments=siteid,v,fd,td,l"
        
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        print("Page load command sent.")
        
        # 3. Sort by Date
        print("Waiting for table...")
        try:
            # Increased timeout to 60s
            wait = WebDriverWait(driver, 60)
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="results-table"]')))
            print("Table found!")
        except Exception as e:
            print(f"Table not found within timeout: {e}")
            driver.save_screenshot(os.path.join(CURRENT_DIR, "error_screenshot.png"))
            print(f"Saved error screenshot to {os.path.join(CURRENT_DIR, 'error_screenshot.png')}")
            raise

        print("Attempting to sort by Date (Descending)...")
        # Try to find header with text 'תאריך'
        try:
            date_header_xpath = "//th[contains(text(), 'תאריך')]"
            date_header = wait.until(EC.element_to_be_clickable((By.XPATH, date_header_xpath)))
            print("Date header found, clicking...")
            
            # JS Click to avoid interception
            driver.execute_script("arguments[0].click();", date_header)
            time.sleep(2)
            print("Clicked date header (JS).")
            
            sort_class = date_header.get_attribute("class")
            print(f"Sort class after click: {sort_class}")
            
            if "desc" not in sort_class:
                print("Header not yet desc, clicking again (JS)...")
                driver.execute_script("arguments[0].click();", date_header)
                time.sleep(2)
                
            print("Table sorted.")
            
        except Exception as e:
            print(f"Warning: Could not sort by date header: {e}")

        # 4. Scrape & Identify New Items
        # Load anchor
        state = load_last_meeting_state()
        last_anchor_num = state.get("last_meeting_number")
        last_anchor_date = state.get("last_meeting_date")
        
        print(f"Last processed anchor: {last_anchor_num} ({last_anchor_date})")
        
        rows = driver.find_elements(By.XPATH, '//*[@id="results-table"]/tbody/tr')
        print(f"Found {len(rows)} rows.")
        
        # We iterate from top (newest after sort)
        new_meetings_found_metadata = []
        
        for row_elem in rows:
            try:
                # Extract details (User requested: Col 3=Type, Col 4=Date)
                cols = row_elem.find_elements(By.TAG_NAME, "td")
                if len(cols) < 5:
                    continue
                
                # Col indexes (0-based):
                # 0: Icon/Link
                # 1: Meeting Number
                # 2: Committee/Type (User: 3rd column)
                # 3: Date (User: 4th column)
                
                meeting_num_elem = cols[1].find_element(By.TAG_NAME, "a")
                meeting_num = meeting_num_elem.text.strip()
                meeting_type = cols[2].text.strip()
                meeting_date = cols[3].text.strip()
                
                # Check Anchor
                if meeting_num == last_anchor_num and meeting_date == last_anchor_date:
                    print(f"Found anchor meeting {meeting_num}. Stopping list scan.")
                    break
                
                print(f"New Meeting Identified: {meeting_num} ({meeting_type}) on {meeting_date}")
                
                new_meetings_found_metadata.append({
                    "Meeting Number": meeting_num,
                    "Meeting Type": meeting_type,
                    "Date": meeting_date
                })
                    
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        # 5. Process Found Meetings (Reverse order: Oldest -> Newest)
        if not new_meetings_found_metadata:
            print("No new meetings found.")
            return

        print(f"Processing {len(new_meetings_found_metadata)} new meetings...")
        
        # Load existing global data
        all_data = pdf_analyzer.load_existing_data()
        existing_keys = {(m['metadata']['meeting_id'], m['metadata']['meeting_date']) for m in all_data}
        daily_report_items = []

        for meeting_meta in reversed(new_meetings_found_metadata): 
            m_num = meeting_meta['Meeting Number']
            m_type = meeting_meta['Meeting Type']
            m_date = meeting_meta['Date']
            
            # Double check already processed
            if (m_num, m_date) in existing_keys:
                print(f"Skipping {m_num} ({m_date}) - Already processed (in existing DB).")
                continue
            
            # Download Protocols
            downloaded_files = download_meeting_protocols_via_ui(driver, m_num, m_date, PDF_DIR) # Updated sig
            
            if not downloaded_files:
                print(f"Warning: No protocols downloaded for {m_num}. Moving to next.")
                continue
            
            # Process each downloaded file
            for f_info in downloaded_files:
                local_f = f_info['filename']
                pdf_url = f_info['pdf_url']
                
                row_data_for_analyzer = {
                    'Meeting Number': m_num,
                    'Meeting Type': m_type,
                    'Date': m_date,
                    'Local Filename': local_f,
                    'PDF Download URL': pdf_url,
                    'Original Link': driver.current_url
                }
                
                res = pdf_analyzer.process_row(row_data_for_analyzer)
                if res:
                    all_data.append(res)
                    daily_report_items.append(res)
            
            # Update existing keys so we don't re-process duplicates within run
            existing_keys.add((m_num, m_date))
        
        if not daily_report_items:
            print("No new items to report.")
        else:
            # Save Unified
            pdf_analyzer.save_unified_json(all_data)
            
            # Save Daily Report
            today_str = datetime.now().strftime("%Y-%m-%d")
            daily_report_path = PROCESSED_JSON_DIR / f"daily_report_{today_str}.json"
            with open(daily_report_path, 'w', encoding='utf-8') as f:
                json.dump({"date": today_str, "new_items": daily_report_items}, f, indent=4, ensure_ascii=False)
            print(f"Daily report saved to {daily_report_path}")
        
        # Update Anchor (Newest Meeting)
        if new_meetings_found_metadata:
            newest_meeting = new_meetings_found_metadata[0]
            save_last_meeting_state(newest_meeting['Meeting Number'], newest_meeting['Date'])
            print(f"Updated anchor to: {newest_meeting['Meeting Number']} ({newest_meeting['Date']})")

    except Exception as e:
        print(f"Critical Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        if driver:
            driver.quit()
        if proxy_plugin and os.path.exists(proxy_plugin):
            os.remove(proxy_plugin)
            
if __name__ == "__main__":
    if not PDF_DIR.exists():
        os.makedirs(PDF_DIR)
    run_daily_scan()
