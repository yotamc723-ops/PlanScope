import csv
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Try to import ChromeDriverManager, fallback if it fails
try:
    from webdriver_manager.chrome import ChromeDriverManager
    USE_WEBDRIVER_MANAGER = True
except Exception as e:
    print(f"Warning: Could not initialize ChromeDriverManager due to environment encoding issues: {e}")
    print("Trying to proceed with default system chrome driver...")
    USE_WEBDRIVER_MANAGER = False

def scrape_bat_yam_taba():
    # הגדרות Selenium Headless
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Headless mode enabled
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--remote-debugging-port=9222") # Fix for some chromedriver crashes
    chrome_options.add_argument("--window-size=1920,1080")

    # אתחול הדרייבר
    try:
        if USE_WEBDRIVER_MANAGER:
            driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
        else:
            # Fallback to system Chrome driver
            driver = webdriver.Chrome(options=chrome_options)
    except Exception as e:
        print(f"Error initializing Chrome driver: {e}")
        print("Make sure Chrome is installed and chromedriver is in your PATH")
        return
    
    # תיקון כתובת האתר - הוספת הדומיין המלא
    base_url = "https://batyam.complot.co.il/binyan/#search/GetTabaByNumber&siteid=81&n=502&l=true&arguments=siteid,n,l"
    
    results_data = []

    try:
        print(f"מתחבר לאתר: {base_url}")
        driver.get(base_url)
        wait = WebDriverWait(driver, 20)

        # שלב 1: חיפוש הנתונים (נניח שהחיפוש בוצע או שיש להזין 502)
        # אם יש צורך להזין 502 בתיבת החיפוש לפני, ניתן להוסיף כאן לוגיקה.
        # בהנחה שאתה כבר בעמוד התוצאות כפי שציינת:

        # שלב 2: שינוי ל-100 תוצאות בעמוד
        print("משנה תצוגה ל-100 תוצאות...")
        try:
            select_element = wait.until(EC.presence_of_element_located((By.XPATH, '//*[@id="results-table_length"]/label/select')))
            select = Select(select_element)
            select.select_by_value("100")
            # המתנה קלה לטעינה מחדש של הטבלה
            time.sleep(3)
        except Exception as e:
             print(f"לא נמצאה אפשרות לשינוי מספר השורות (אולי הטבלה כבר טעונה או ריקה?): {e}")

        # שלב חדש: לחיצה על כפתור "ללחוץ כאן" לחיפוש ללא הגבלה
        try:
            print("לוחץ על כפתור לחיפוש ללא הגבלה...")
            unlimited_link = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'getUnlimitedSearch')]")))
            driver.execute_script("arguments[0].click();", unlimited_link)
            print("   נלחץ בהצלחה. ממתין לטעינה...")
            time.sleep(5) # המתנה לטעינה מחדש של הטבלה
        except Exception as e:
            print(f"⚠️ הערה: לא נמצא או לא ניתן ללחוץ על קישור החיפוש ללא הגבלה: {e}")

        page_num = 1
        while True:
            print(f"סורק עמוד מספר {page_num}...")
            
            # המתנה שהטבלה תהיה נוכחת
            try:
                wait.until(EC.presence_of_element_located((By.ID, "results-table")))
            except:
                print("הטבלה לא נמצאה. ייתכן והאתר לא נטען כראוי או שאין תוצאות.")
                break
            
            # שליפת כל השורות בגוף הטבלה
            rows = driver.find_elements(By.XPATH, '//*[@id="results-table"]/tbody/tr')
            
            if not rows:
                print("לא נמצאו שורות בטבלה.")
                break

            for index, row in enumerate(rows, start=1):
                try:
                    # חילוץ המספר הסידורי מה-href (עמודה 1)
                    link_element = row.find_element(By.XPATH, './td[1]/a')
                    href_content = link_element.get_attribute('href') # דוגמה: javascript:getTaba(2037)
                    
                    # שימוש ב-Regex לחילוץ המספר בתוך הסוגריים
                    match = re.search(r'\((\d+)\)', href_content)
                    serial_number = match.group(1) if match else "N/A"
                    
                    # חילוץ מספר התב"ע (עמודה 2)
                    taba_number = row.find_element(By.XPATH, './td[2]/a').text.strip()
                    
                    results_data.append({
                        'Taba_Number': taba_number,
                        'Serial_ID': serial_number
                    })
                except Exception as e:
                    # התעלמות משגיאות נקודתיות כדי לא לעצור את הריצה
                    pass

            # שלב 3: בדיקה אם יש כפתור "הבא" ולחיצה עליו
            try:
                # מציאת הכפתור לפי ID (שהוא כנראה הכפתור עצמו או ה-a)
                # לפי הבדיקה, ה-ID הוא results-table_next
                next_button = wait.until(EC.presence_of_element_located((By.ID, 'results-table_next')))
                
                # בדיקה אם הכפתור מושבת (מחלקת disabled)
                # לפעמים המחלקה disabled נמצאת על האלמנט עצמו או על ההורה
                if 'disabled' in next_button.get_attribute('class'):
                    print(f"הגענו לעמוד האחרון (עמוד {page_num}).")
                    break
                
                # בדיקה נוספת: אם זה תג li וה-a בתוכו מושבת (מבנה נפוץ ב-DataTables)
                # אבל אם ה-ID הוא על הכפתור, הבדיקה הראשונה תספיק.
                
                # גלילה לכפתור (ללא smooth)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center', inline: 'nearest'});", next_button)
                time.sleep(1)
                
                # לחיצה באמצעות JavaScript (הכי אמין ב-Headless)
                driver.execute_script("arguments[0].click();", next_button)
                
                # המתנה שהטבלה תיטען מחדש (זיהוי שינוי או סתם המתנה)
                time.sleep(4)
                page_num += 1

            except Exception as e:
                print(f"סיום הסריקה (לא נמצא כפתור 'הבא' או שגיאה במעבר): {e}")
                break

        # שמירה לקובץ CSV
        save_to_csv(results_data)

    finally:
        driver.quit()

def save_to_csv(data):
    filename = 'bat_yam_taba_list.csv'
    keys = ['Taba_Number', 'Serial_ID']
    
    with open(filename, 'w', newline='', encoding='utf-8-sig') as output_file:
        dict_writer = csv.DictWriter(output_file, fieldnames=keys)
        dict_writer.writeheader()
        dict_writer.writerows(data)
    
    print(f"הסריקה הושלמה! {len(data)} רשומות נשמרו לקובץ {filename}")

if __name__ == "__main__":
    scrape_bat_yam_taba()