import time
import os
import json
import random
import string
import zipfile
from pathlib import Path
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables (logic copied from analyze_permits.py)
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

# Proxy Config
USE_PROXY = True
PROXY_HOST = os.getenv("PROXY_HOST", "brd.superproxy.io")
PROXY_PORT = os.getenv("PROXY_PORT", "33335")
PROXY_USER = os.getenv("PROXY_USER")
PROXY_PASS = os.getenv("PROXY_PASS")

def get_proxy_auth_extension(proxy_host, proxy_port, proxy_user, proxy_pass):
    """
    Creates a Chrome extension (zip file) to handle proxy authentication.
    Returns the path to the created extension.
    """
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
        "minimum_chrome_version":"22.0.0"
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
            bypassList: ["localhost"]
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
    
    plugin_file = 'proxy_auth_plugin.zip'
    with zipfile.ZipFile(plugin_file, 'w') as zp:
        zp.writestr("manifest.json", manifest_json)
        zp.writestr("background.js", background_js)
    
    return os.path.abspath(plugin_file)

def get_proxy_details(session_id=None):
    """
    Constructs the proxy user string with session rotation (same logic as analyze_permits.py).
    """
    if not USE_PROXY:
        print("⚠️ Proxy disabled in code.")
        return None
        
    current_user = PROXY_USER
    if not current_user or not PROXY_PASS:
        print("⚠️ Proxy enabled but credentials missing.")
        return None

    # Bright Data Logic
    if 'brd-customer' in current_user:
        if '-country-' not in current_user:
            current_user = f"{current_user}-country-il"
        
        if session_id:
            current_user = f"{current_user}-session-{session_id}"
            
    return {
        "host": PROXY_HOST,
        "port": PROXY_PORT,
        "user": current_user,
        "pass": PROXY_PASS
    }


PERMIT_JSON = "permit_numbers.json"

def load_existing_permits():
    """Load existing permit numbers from JSON file."""
    existing = set()
    if os.path.exists(PERMIT_JSON):
        try:
            with open(PERMIT_JSON, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for permit in data:
                        existing.add(str(permit).strip())
        except Exception as e:
            print(f"Warning: Could not read existing permits from {PERMIT_JSON}: {e}")
    return existing

def save_permits_to_json(permit_set):
    """Save all permits to JSON file."""
    try:
        # Sort for consistency
        sorted_permits = sorted(list(permit_set))
        with open(PERMIT_JSON, "w", encoding="utf-8") as f:
            json.dump(sorted_permits, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"Error saving to JSON: {e}")

def scrape_permit_numbers():
    # Load existing permit numbers
    existing_permits = load_existing_permits()
    initial_count = len(existing_permits)
    print(f"Loaded {initial_count} existing permit numbers from {PERMIT_JSON}")
    
    # Chrome Headless Settings
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # User-Agent to avoid blocking
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    # Proxy Setup
    if USE_PROXY:
        session_id = ''.join(random.choices(string.ascii_lowercase + string.digits, k=8))
        proxy_details = get_proxy_details(session_id=session_id)
        
        if proxy_details:
            print(f"🔒 Configuring Proxy: {proxy_details['host']}:{proxy_details['port']} (Session: {session_id})")
            
            # Create and add authentication extension
            plugin_path = get_proxy_auth_extension(
                proxy_details['host'], 
                proxy_details['port'], 
                proxy_details['user'], 
                proxy_details['pass']
            )
            chrome_options.add_extension(plugin_path)
            
            # Note: Do NOT use --proxy-server argument when using the extension for auth
    
    driver = webdriver.Chrome(options=chrome_options)

    # Clean up the extension file
    if os.path.exists('proxy_auth_plugin.zip'):
        try:
            os.remove('proxy_auth_plugin.zip')
        except: pass
    
    # List to keep track of new permits found in this session
    new_permits = []
    
    try:
        # 1. Search URL
        url = "https://batyam.complot.co.il/iturbakashot/#search/GetBakashotByNumber&siteid=81&grp=0&t=0&b=2026&l=true&arguments=siteId,grp,t,b,l"
        print(f"Connecting to {url}...")
        driver.get(url)

        # 2. Click "Show All"
        try:
            show_all_xpath = '//*[@id="request-list-container"]/p[1]/a'
            show_all_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, show_all_xpath))
            )
            driver.execute_script("arguments[0].click();", show_all_btn)
            print("Clicked 'Show All' via JS. Waiting for table update...")
            time.sleep(5) 
            
        except TimeoutException:
            print("'Show All' button not found. Assuming list is already full or empty.")
        except Exception as e:
            print(f"Error clicking 'Show All': {e}")

        # 3. Pagination Loop
        page_num = 1
        while True:
            print(f"Scraping page {page_num}...")
            
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="results-table"]/tbody/tr'))
            )
            
            rows = driver.find_elements(By.XPATH, '//*[@id="results-table"]/tbody/tr')
            
            for row in rows:
                try:
                    link_element = row.find_element(By.XPATH, './td[2]/a')
                    permit_number = link_element.text.strip()
                    
                    if permit_number and len(permit_number) == 8 and (permit_number.startswith('2025') or permit_number.startswith('2026')):
                        if permit_number not in existing_permits:
                            new_permits.append(permit_number)
                            existing_permits.add(permit_number)
                            
                            # Save immediately to JSON (rewrite file with full set)
                            save_permits_to_json(existing_permits)
                            
                            print(f"Found NEW: {permit_number} (saved to JSON)")
                        else:
                            print(f"Found (already exists): {permit_number}")
                    elif permit_number:
                        print(f"Skipped (wrong format): {permit_number}")
                except NoSuchElementException:
                    continue

            # 4. Next Button
            try:
                next_btn_xpath = '//*[@id="results-table_next"]'
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, next_btn_xpath))
                )
                
                class_attr = next_button.get_attribute("class")
                if "disabled" in class_attr:
                    print("Reached last page (Next button disabled). Done.")
                    break
                
                driver.execute_script("arguments[0].click();", next_button)
                print(f"Clicked 'Next' (Page {page_num} done). Loading next page...")
                page_num += 1
                time.sleep(3) 
                
            except TimeoutException:
                print("Next button not found via XPath. Ending scrape.")
                break
            except Exception as e:
                print(f"Error clicking Next: {e}")
                break

    except Exception as e:
        print(f"Critical Error: {e}")
        
    finally:
        driver.quit()
        
        # Final summary
        total_count = len(existing_permits)
        print(f"\nDone! Found {len(new_permits)} new permits.")
        print(f"Total permits in JSON: {total_count} (started with {initial_count})")

if __name__ == "__main__":
    scrape_permit_numbers()