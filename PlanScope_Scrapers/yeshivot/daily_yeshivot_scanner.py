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

def wait_for_download(download_dir, timeout=60):
    """
    Waits for a file to appear in the directory (that is not a .crdownload).
    Returns the path to the newest file.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        files = glob.glob(os.path.join(download_dir, "*"))
        files = [f for f in files if not f.endswith(".crdownload") and not f.endswith(".tmp")]
        files.sort(key=os.path.getmtime, reverse=True)
        
        if files:
            # Check if file relies on stable size (download finished)
            latest_file = files[0]
            # Simple check: wait 2 seconds and verify size didn't change (basic)
            # Better check: .crdownload gone implies Chrome finished.
            return latest_file
        time.sleep(1)
    return None

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

    proxy_plugin = None
    if USE_PROXY and PROXY_USER and PROXY_PASS:
        print("Using Proxy...")
        proxy_plugin = get_proxy_auth_extension(PROXY_HOST, PROXY_PORT, PROXY_USER, PROXY_PASS)
        chrome_options.add_extension(proxy_plugin)
    
    driver = None
    new_items_processed = []
    
    try:
        if HAS_MANAGER:
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            driver = webdriver.Chrome(options=chrome_options)
            
        wait = WebDriverWait(driver, 30)

        # 2. Construct Query URL
        # We look back 30 days and forward 30 days to cover recent past and near future meetings
        today = datetime.now()
        start_date = (today - timedelta(days=60)).strftime("%d/%m/%Y") # Extended check 
        end_date = (today + timedelta(days=60)).strftime("%d/%m/%Y")   # Extended check
        
        base_url = "https://batyam.complot.co.il/yeshivot/#search/GetMeetingByDate"
        # dynamic params
        target_url = f"{base_url}&siteid=81&v=0&fd={start_date}&td={end_date}&l=true"
        
        print(f"Navigating to: {target_url}")
        driver.get(target_url)
        print("Page load command sent.")
        
        # 3. Sort by Date
        print("Waiting for table...")
        try:
            wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="results-table"]')))
            print("Table found!")
        except Exception as e:
            print(f"Table not found within timeout: {e}")
            raise

        print("Attempting to sort by Date (Descending)...")
        # Try to find header with text 'תאריך'
        try:
            date_header_xpath = "//th[contains(text(), 'תאריך')]"
            date_header = wait.until(EC.element_to_be_clickable((By.XPATH, date_header_xpath)))
            print("Date header found, clicking...")
            
            # Click once (usually Ascending or Descending toggle)
            date_header.click()
            time.sleep(2)
            print("Clicked date header once.")
            
            sort_class = date_header.get_attribute("class")
            print(f"Sort class after click: {sort_class}")
            
            if "desc" not in sort_class:
                print("Header not yet desc, clicking again...")
                date_header.click()
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
        new_meetings_found = []
        
        for row_elem in rows:
            try:
                # Extract details
                # Columns: 
                # 1: ? (Checkbox/Icon)
                # 2: Mispar Yeshiva (Link)
                # 3: Committee Name
                # 4: Date
                # 5: Day
                # 6: Time
                # 7: Location
                # 8: Status/Protocol Link containing "פרוטוקול החלטות"
                
                cols = row_elem.find_elements(By.TAG_NAME, "td")
                if len(cols) < 5:
                    continue
                
                meeting_num_elem = cols[1].find_element(By.TAG_NAME, "a")
                meeting_num = meeting_num_elem.text.strip()
                meeting_date = cols[3].text.strip()
                
                # Check Anchor
                if meeting_num == last_anchor_num and meeting_date == last_anchor_date:
                    print("Found anchor meeting. Stopping scan.")
                    break
                
                # Check for "פרוטוקול החלטות" link
                # Sometimes it's in a specific column or just a link with text
                protocol_link_elem = None
                try:
                    protocol_link_elem = row_elem.find_element(By.XPATH, ".//a[contains(text(), 'פרוטוקול החלטות')]")
                except:
                    pass
                
                if not protocol_link_elem:
                    # No protocol available yet
                    continue
                    
                print(f"New Meeting Found: {meeting_num} on {meeting_date}")
                
                # Download
                # Store current file count/names to identify new file
                existing_files = set(os.listdir(PDF_DIR))
                protocol_link_elem.click()
                
                # Wait for download
                downloaded_file = None
                end_wait = time.time() + 30
                while time.time() < end_wait:
                    current_files = set(os.listdir(PDF_DIR))
                    new_files = current_files - existing_files
                    real_new = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
                    if real_new:
                        downloaded_file = real_new[0]
                        break
                    time.sleep(1)
                
                if downloaded_file:
                    print(f"Downloaded: {downloaded_file}")
                    
                    # Prepare Data for Analyzer
                    # pdf_analyzer.process_row expects a dict with specific keys
                    # "Original Link" is mostly for metadata, we can put the page URL or empty
                    
                    row_data = {
                        'Meeting Number': meeting_num,
                        'Date': meeting_date,
                        'Local Filename': downloaded_file,
                        'Original Link': target_url
                    }
                    
                    new_meetings_found.append(row_data)
                else:
                    print("Timeout waiting for file download.")
                    
            except Exception as e:
                print(f"Error processing row: {e}")
                continue
        
        # 5. Process Found Meetings (Reverse order: Oldest -> Newest)
        # This ensures if we crash, we saved the older ones first? 
        # Actually existing Logic just appends. 
        # But for 'last_meeting' update, we want the ABSOLUTE newest (top of the list found) to be saved at the end.
        
        if not new_meetings_found:
            print("No new meetings found.")
            return

        print(f"Processing {len(new_meetings_found)} new meetings...")
        
        # Load existing global data
        all_data = pdf_analyzer.load_existing_data()
        existing_keys = {(m['metadata']['meeting_id'], m['metadata']['meeting_date']) for m in all_data}
        daily_report_items = []

        # Process from Newest found to Oldest found? 
        # User list `new_meetings_found` is [MostRecent, ..., LeastRecent] (from table top-down)
        # Verify: If table is DESC, first row is Newest.
        # We collected them in that order. 
        # So `new_meetings_found[0]` is the Newest.
        
        # We should append meaningful items.
        
        for meeting_row in reversed(new_meetings_found): # Process Oldest -> Newest
            # Check for duplicates in existing data to avoid re-processing
            if (meeting_row['Meeting Number'], meeting_row['Date']) in existing_keys:
                print(f"Skipping {meeting_row['Meeting Number']} ({meeting_row['Date']}) - Already processed.")
                continue

            res = pdf_analyzer.process_row(meeting_row)
            if res:
                all_data.append(res)
                daily_report_items.append(res)
                # Update existing keys to prevent duplicates within this run if any
                existing_keys.add((meeting_row['Meeting Number'], meeting_row['Date']))
        
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
        # Even if we skipped it (because we might have processed it in a previous partial run or it was in history),
        # we still want to update our anchor to the newest one found on the page so next time we stop there.
        if new_meetings_found:
            newest_meeting = new_meetings_found[0]
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
