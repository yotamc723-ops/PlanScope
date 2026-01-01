import time
import os
import sys
import json
from collections import Counter
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ניסיון לעקוף שגיאות קידוד של קבצי .env שקיימים בתיקייה
try:
    from webdriver_manager.chrome import ChromeDriverManager
    HAS_MANAGER = True
except Exception as e:
    print(f"Warning: Could not initialize ChromeDriverManager due to environment encoding issues: {e}")
    print("Trying to proceed with default system chrome driver...")
    HAS_MANAGER = False

def run_scraper():
    # הגדרות עבור Selenium במצב Headless (מתאים לשרת)
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # מניעת זיהוי כבוט
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    
    driver = None
    try:
        if HAS_MANAGER:
            # אתחול הדרייבר באמצעות DriverManager
            service = Service(ChromeDriverManager().install())
            driver = webdriver.Chrome(service=service, options=chrome_options)
        else:
            # ניסיון הרצה ללא Manager
            driver = webdriver.Chrome(options=chrome_options)
        
        # הכתובת המבוקשת עם הפרמטרים של התאריכים
        target_url = "https://batyam.complot.co.il/yeshivot/#search/GetMeetingByDate&siteid=81&v=0&fd=01/01/2025&td=30/01/2026&l=true&arguments=siteid,v,fd,td,l"
        
        print(f"Connecting to: {target_url}...")
        driver.get(target_url)
        
        # המתנה לטעינת הטבלה
        wait = WebDriverWait(driver, 25)
        
        # שלב 1: שינוי התצוגה ל-100 תוצאות
        print("Setting view to 100 results...")
        try:
            dropdown_xpath = '//*[@id="results-table_length"]/label/select'
            wait.until(EC.presence_of_element_located((By.XPATH, dropdown_xpath)))
            
            option_100 = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="results-table_length"]/label/select/option[4]')))
            option_100.click()
            
            # המתנה קלה לעדכון הטבלה לאחר לחיצה
            time.sleep(4)
        except Exception as e:
            print(f"Notice: Could not set view to 100. Proceeding with current view. Error: {e}")
        
        # שלב 2: איסוף הנתונים
        wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="results-table"]/tbody/tr')))
        
        rows = driver.find_elements(By.XPATH, '//*[@id="results-table"]/tbody/tr')
        meeting_numbers = []
        
        print(f"Detected {len(rows)} rows. Extracting 8-digit committee numbers...")
        
        for i in range(1, len(rows) + 1):
            try:
                # ה-XPATH שסיפקת לחילוץ המספר (עמודה שנייה)
                xpath_link = f'//*[@id="results-table"]/tbody/tr[{i}]/td[2]/a'
                element = driver.find_element(By.XPATH, xpath_link)
                number = element.text.strip()
                
                # סינון: רק אם המחרוזת באורך 8 ומכילה ספרות בלבד
                if number and len(number) == 8 and number.isdigit():
                    meeting_numbers.append(number)
            except Exception:
                continue
        
        # שלב 3: עיבוד נתונים ושמירה
        
        # א. שמירת רשימה מלאה לקובץ טקסט (לשימוש הסורק השני)
        output_txt = "meeting_numbers.txt"
        with open(output_txt, "w", encoding="utf-8") as f:
            for num in meeting_numbers:
                f.write(num + "\n")
        
        # ב. יצירת JSON עם ספירת מופעים לכל ישיבה
        meeting_counts = Counter(meeting_numbers)
        output_json = "meeting_counts.json"
        
        with open(output_json, "w", encoding="utf-8") as f:
            json.dump(meeting_counts, f, indent=4, ensure_ascii=False)
            
        print(f"Success! Collected {len(meeting_numbers)} numbers.")
        print(f"Raw list saved to: {output_txt}")
        print(f"Counts JSON saved to: {output_json}")
        
    except Exception as e:
        print(f"An error occurred during execution: {e}")
        
    finally:
        if driver:
            driver.quit()

if __name__ == "__main__":
    run_scraper()