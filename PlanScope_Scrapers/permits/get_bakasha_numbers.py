import time
import os
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

def load_existing_permits():
    """Load existing permit numbers from file."""
    existing = set()
    if os.path.exists("permit_numbers.txt"):
        try:
            with open("permit_numbers.txt", "r", encoding="utf-8") as f:
                for line in f:
                    permit = line.strip()
                    if permit:
                        existing.add(permit)
        except Exception as e:
            print(f"Warning: Could not read existing permits: {e}")
    return existing

def scrape_permit_numbers():
    # Load existing permit numbers
    existing_permits = load_existing_permits()
    initial_count = len(existing_permits)
    print(f"Loaded {initial_count} existing permit numbers from permit_numbers.txt")
    
    # הגדרות Chrome Headless (ללא פתיחת דפדפן)
    chrome_options = Options()
    chrome_options.add_argument("--headless") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    # שינוי User-Agent כדי לא להיחסם
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    driver = webdriver.Chrome(options=chrome_options)
    
    # רשימה לשמירת המספרים החדשים שנמצאו
    new_permits = []
    
    try:
        # 1. כניסה לכתובת החיפוש
        url = "https://batyam.complot.co.il/iturbakashot/#search/GetBakashotByNumber&siteid=81&grp=0&t=0&b=2026&l=true&arguments=siteId,grp,t,b,l"
        print(f"Connecting to {url}...")
        driver.get(url)

        # 2. לחיצה על "הצג הכל"
        # 2. לחיצה על "הצג הכל" - גרסה עמידה לשגיאות
        try:
            # שיניתי את ה-XPATH טיפה כדי לתפוס את הלינק (a) ולא את הטקסט המודגש (strong)
            # זה בדרך כלל עובד טוב יותר
            show_all_xpath = '//*[@id="request-list-container"]/p[1]/a'
            
            # מחכים שהאלמנט יהיה קיים (לא חייב להיות לחיץ בשיטה הזאת, רק קיים ב-DOM)
            show_all_btn = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, show_all_xpath))
            )
            
            # --- כאן התיקון: שימוש ב-JavaScript במקום click() רגיל ---
            driver.execute_script("arguments[0].click();", show_all_btn)
            # --------------------------------------------------------
            
            print("Clicked 'Show All' via JS. Waiting for table update...")
            time.sleep(5) # נתתי לו קצת יותר זמן לנשום אחרי הלחיצה
            
        except TimeoutException:
            print("'Show All' button not found. Assuming list is already full or empty.")
        except Exception as e:
            print(f"Error clicking 'Show All': {e}")
        # 3. לולאת ריצה על העמודים
        page_num = 1
        while True:
            print(f"Scraping page {page_num}...")
            
            # המתנה לטעינת השורות בטבלה
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="results-table"]/tbody/tr'))
            )
            
            rows = driver.find_elements(By.XPATH, '//*[@id="results-table"]/tbody/tr')
            
            # מעבר על כל שורה ושליפת המספר (מהעמודה השנייה - td[2])
            for row in rows:
                try:
                    # ה-XPATH היחסי בתוך השורה
                    link_element = row.find_element(By.XPATH, './td[2]/a')
                    permit_number = link_element.text.strip()
                    # Only keep 8-digit permit numbers that start with 2025 or 2026
                    if permit_number and len(permit_number) == 8 and (permit_number.startswith('2025') or permit_number.startswith('2026')):
                        # Check if permit already exists
                        if permit_number not in existing_permits:
                            # New permit found - add to list and append to file
                            new_permits.append(permit_number)
                            existing_permits.add(permit_number)  # Add to set to avoid duplicates in same run
                            
                            # Append immediately to file
                            with open("permit_numbers.txt", "a", encoding="utf-8") as f:
                                f.write(f"{permit_number}\n")
                            
                            print(f"Found NEW: {permit_number} (appended to file)")
                        else:
                            print(f"Found (already exists): {permit_number}")
                    elif permit_number:
                        print(f"Skipped (wrong format): {permit_number}")
                except NoSuchElementException:
                    continue

# 4. הבלוק המתוקן לכפתור "הבא" (Next Button)
            try:
                next_btn_xpath = '//*[@id="results-table_next"]'
                
                # מוודאים שהכפתור קיים ב-DOM
                next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, next_btn_xpath))
                )
                
                # בדיקה האם הגענו לסוף (הכפתור קיים אבל כבוי)
                class_attr = next_button.get_attribute("class")
                if "disabled" in class_attr:
                    print("Reached last page (Next button disabled). Done.")
                    break
                
                # --- התיקון: לחיצה אגרסיבית עם JavaScript ---
                # זה עוקף כל אלמנט שמסתיר את הכפתור (כמו פוטר או באנר)
                driver.execute_script("arguments[0].click();", next_button)
                # --------------------------------------------
                
                print(f"Clicked 'Next' (Page {page_num} done). Loading next page...")
                page_num += 1
                
                # חשוב: זמן המתנה שהטבלה החדשה תיטען לפני שמתחילים שוב
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
        print(f"Total permits in file: {total_count} (started with {initial_count})")

if __name__ == "__main__":
    scrape_permit_numbers()