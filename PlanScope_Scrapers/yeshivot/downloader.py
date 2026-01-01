import time
import os
import json
import glob
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_MANAGER = True
except Exception:
    HAS_MANAGER = False

def setup_downloader():
    # יצירת תיקיית היעד אם היא לא קיימת
    download_dir = os.path.join(os.getcwd(), "decision_protocols")
    if not os.path.exists(download_dir):
        os.makedirs(download_dir)
        print(f"Created directory: {download_dir}")
    
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    prefs = {
        "download.default_directory": download_dir,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "plugins.always_open_pdf_externally": True
    }
    chrome_options.add_experimental_option("prefs", prefs)
    
    if HAS_MANAGER:
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
    else:
        driver = webdriver.Chrome(options=chrome_options)

    driver.execute_cdp_cmd("Page.setDownloadBehavior", {
        "behavior": "allow",
        "downloadPath": download_dir
    })
    
    return driver, download_dir

def wait_for_new_file(download_dir, old_files, timeout=30):
    """
    ממתין לקובץ חדש בתיקייה, ומחזיר את שמו המקורי כפי שירד.
    לא מתבצע שינוי שם לקובץ.
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        current_files = set(os.listdir(download_dir))
        new_files = current_files - old_files
        
        # סינון קבצים זמניים
        valid_new_files = [f for f in new_files if not f.endswith('.crdownload') and not f.endswith('.tmp')]
        
        if valid_new_files:
            # מניחים שיורד קובץ אחד בכל פעם
            new_filename = valid_new_files[0]
            
            # המתנה קצרה לוודא שהקובץ סגור ומוכן
            time.sleep(1) 
            
            print(f"File downloaded successfully: {new_filename}")
            return new_filename
        
        time.sleep(1)
    
    print("Download timed out.")
    return None

def run_downloader():
    input_json = "meeting_counts.json"
    input_txt = "meeting_numbers.txt"
    
    meeting_data = {}
    
    if os.path.exists(input_json):
        print(f"Loading meeting counts from {input_json}...")
        with open(input_json, "r", encoding="utf-8") as f:
            meeting_data = json.load(f)
    elif os.path.exists(input_txt):
        print(f"Warning: {input_json} not found. Falling back to {input_txt}.")
        with open(input_txt, "r") as f:
            lines = [line.strip() for line in f if line.strip()]
            meeting_data = {m: 1 for m in lines}
    else:
        print("Error: No input files found.")
        return

    driver, download_dir = setup_downloader()
    all_meetings_output = []

    try:
        for m_number, expected_count in meeting_data.items():
            print(f"\n--- Processing meeting: {m_number} (Expected files: {expected_count}) ---")
            
            found_files = 0
            consecutive_failures = 0
            current_v = 1
            
            # לולאה להורדת קבצים
            while found_files < expected_count and consecutive_failures < 3:
                
                api_url = f"https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetMeetingDocs&siteid=81&v={current_v}&m={m_number}&arguments=siteid,v,m"
                driver.get(api_url)
                
                try:
                    wait = WebDriverWait(driver, 5)
                    
                    # חיפוש שורה המכילה "פרוטוקול החלטות"
                    protocol_xpath = "//a[contains(., 'פרוטוקול החלטות')]"
                    download_link_element = wait.until(EC.element_to_be_clickable((By.XPATH, protocol_xpath)))
                    
                    # מציאת אלמנט השורה (tr) כדי לשלוף ממנו את התאריך
                    row_element = download_link_element.find_element(By.XPATH, "./ancestor::tr")
                    
                    # שליפת התאריך מהעמודה השלישית באותה שורה
                    date_element = row_element.find_element(By.XPATH, "./td[3]")
                    meeting_date = date_element.text.strip()
                    
                    # שליפת הקישור
                    pdf_url = download_link_element.get_attribute('href')
                    
                    print(f"Found 'Decision Protocol' for v={current_v} (Date: {meeting_date})")
                    
                    # שמירת מצב הקבצים לפני ההורדה
                    before_download_files = set(os.listdir(download_dir))
                    
                    # ביצוע ההורדה
                    download_link_element.click()
                    
                    # המתנה לקובץ החדש וקבלת שמו (ללא שינוי שם)
                    downloaded_filename = wait_for_new_file(download_dir, before_download_files)
                    
                    if downloaded_filename:
                        meeting_record = {
                            "Meeting Number": m_number,
                            "Date": meeting_date,
                            "Local Filename": downloaded_filename, # השם המקורי כפי שירד למחשב
                            "Original Link": pdf_url,
                            "V Param": current_v
                        }
                        all_meetings_output.append(meeting_record)
                        found_files += 1
                        consecutive_failures = 0 
                    else:
                        consecutive_failures += 1
                        
                except Exception:
                    # לא נמצא פרוטוקול החלטות ב-v הזה
                    consecutive_failures += 1
                
                current_v += 1
            
            if found_files < expected_count:
                print(f"Warning: Expected {expected_count} files for {m_number}, but found {found_files}.")
                
        # שמירת הנתונים ל-JSON ול-CSV
        json_output_file = "basic_data.json"
        csv_file = "meeting_index.csv"
        
        # שמירת JSON
        with open(json_output_file, "w", encoding="utf-8") as json_f:
            json.dump(all_meetings_output, json_f, ensure_ascii=False, indent=4)
            
        # שמירת CSV (אקסל)
        try:
            fieldnames = ["Meeting Number", "Date", "Local Filename", "Original Link", "V Param"]
            with open(csv_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(all_meetings_output)
        except Exception as e:
            print(f"Error creating CSV file: {e}")

        print(f"Finished processing. Data map saved to {json_output_file} and {csv_file}")
        
    finally:
        driver.quit()

if __name__ == "__main__":
    run_downloader()