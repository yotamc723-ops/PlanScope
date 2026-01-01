import csv
import json
import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re
import urllib.parse
from io import StringIO
import os

def clean_text(text):
    if isinstance(text, str):
        return text.strip().replace('\xa0', ' ')
    return text

def extract_mavat_link(onclick_text):
    if not onclick_text:
        return None
    # מחפש את הכתובת בתוך ה-encodeURI
    match = re.search(r"encodeURI\('(.*?)'\)", onclick_text)
    if match:
        return match.group(1)
    
    match_url = re.search(r"(https://mavat\.iplan\.gov\.il/[^\']+)", onclick_text)
    if match_url:
        return match_url.group(1)
        
    return None

def scrape_plan(serial_id, taba_number, max_retries=3):
    url = f"https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetTabaFile&siteid=81&n={serial_id}&arguments=siteid,n"
    
    response = None
    for attempt in range(1, max_retries + 1):
        try:
            response = requests.get(url, timeout=15)
            response.raise_for_status()
            break
        except Exception as e:
            print(f"Attempt {attempt}/{max_retries} failed for ID {serial_id}: {e}")
            if attempt < max_retries:
                time.sleep(2)
            else:
                return None

    if not response:
        return None

    # יצירת אובייקט Soup עבור חלקים שאינם טבלאיים (כותרות) או לינקים מורכבים
    soup = BeautifulSoup(response.content, 'html.parser')
    
    plan_data = {
        "plan_number": taba_number,
        "plan_type": None,
        "plan_name": None,
        "general_info": {},
        "history": []
    }

    # --- 1. חילוץ כותרות (נשאר עם BS4 כי הן בתוך DIVs ולא טבלה) ---
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

    # --- 2. חילוץ מידע כללי באמצעות Pandas (השיטה החדשה) ---
    # ננסה לקרוא את כל הטבלאות בדף בבת אחת
    try:
        dfs = pd.read_html(StringIO(str(soup)))
        
        # מיפוי שדות
        field_mapping = {
            "סטטוס תוכנית": "status",
            "תאריך הסטטוס": "status_date",
            "בסמכות": "authority",
            "שכונה": "neighborhood",
            "שטח": "area",
            "יזם": "developer",
            'קישור למבא"ת': "mavat_link"
        }

        # מעבר על הטבלאות שנמצאו כדי לאתר את טבלת המידע הכללי
        for df in dfs:
            # הופכים למחרוזת כדי לבדוק אם מילות המפתח נמצאות בטבלה הזו
            table_str = df.to_string()
            if "סטטוס תוכנית" in table_str or "תאריך הסטטוס" in table_str:
                # מצאנו את הטבלה הנכונה. לרוב היא בנויה כ-2 עמודות (מפתח, ערך)
                # ננקה ערכי NaN
                df = df.dropna(how='all')
                
                # נעבור שורה שורה בטבלה שאיתרנו
                # מניחים שהעמודה הראשונה היא המפתח והשניה היא הערך (או קומבינציה דומה)
                # read_html לפעמים מזהה שורת כותרת, ולפעמים לא. נתייחס לכל השורות כמידע.
                for index, row in df.iterrows():
                    # לוקחים את שני התאים הראשונים בשורה (מפתח וערך)
                    if len(row) < 2: continue
                    
                    key = clean_text(str(row.iloc[0]))
                    value = clean_text(str(row.iloc[1]))
                    
                    # בדיקה האם המפתח קיים במיפוי
                    for hebrew_key, english_key in field_mapping.items():
                        if hebrew_key in key:
                            plan_data["general_info"][english_key] = value
                break # סיימנו עם טבלת המידע הכללי

    except ValueError:
        pass # לא נמצאו טבלאות בדף

    # --- תיקון ספציפי לקישור מבא"ת ---
    # פנדס מנקה את ה-HTML ומאבדת את ה-onclick. נשלים אותו ידנית עם BS4 אם צריך.
    # זהו "הפינצטה" שמשלימה את "שואב האבק".
    mavat_td = soup.find('td', string=re.compile('קישור למבא"ת'))
    if mavat_td:
        link_td = mavat_td.find_next_sibling('td')
        if link_td:
            anchor = link_td.find('a')
            if anchor and anchor.has_attr('onclick'):
                plan_data["general_info"]["mavat_link"] = extract_mavat_link(anchor['onclick'])

    # --- 3. חילוץ היסטוריה באמצעות Pandas (השיטה החדשה) ---
    # שולפים ישירות את ה-HTML של ה-DIV המכיל את ההיסטוריה
    history_div = soup.find(id="table-shlavim")
    if history_div:
        try:
            # מעבירים לפנדס רק את החלק הרלוונטי
            hist_dfs = pd.read_html(StringIO(str(history_div)))
            
            if hist_dfs:
                hist_df = hist_dfs[0] # הטבלה הראשונה בתוך ה-DIV
                
                # מנקים ומסדרים את המידע
                # פנדס בד"כ מזהה כותרות לבד, אבל אם לא, אפשר לגשת לפי אינדקס
                # נניח שהעמודה ה-0 היא תאריך וה-1 היא שלב (לפי ה-HTML המקורי)
                
                # מוודאים שיש לנו מספיק עמודות
                if len(hist_df.columns) >= 2:
                    # שינוי שמות עמודות לנורמליזציה (למקרה שהכותרות בעברית או חסרות)
                    # אנו לוקחים את העמודה הראשונה והשנייה ללא קשר לשמן
                    hist_df = hist_df.iloc[:, [0, 1]] 
                    hist_df.columns = ["date", "stage"]
                    
                    # המרה למילון וניקוי
                    records = hist_df.to_dict('records')
                    for rec in records:
                        d = clean_text(str(rec['date']))
                        s = clean_text(str(rec['stage']))
                        
                        # סינון שורות ריקות או כותרות שחזרו על עצמן
                        if d and s and "תאריך" not in d: 
                             # Save as compact array [date, stage] instead of object
                             plan_data["history"].append([d, s])
        except ValueError:
            pass # לא נמצאה טבלה בתוך ה-div

    return plan_data

def load_existing_plans(output_json):
    """Load existing scraped plans from JSON file and return set of plan numbers."""
    scraped_plans = set()
    existing_data = []
    
    if os.path.exists(output_json):
        try:
            with open(output_json, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content:
                    existing_data = json.loads(content)
                    # Extract plan numbers from existing data
                    for plan in existing_data:
                        if isinstance(plan, dict) and 'plan_number' in plan:
                            scraped_plans.add(str(plan['plan_number']))
                    print(f"Found {len(scraped_plans)} already scraped plans in {output_json}")
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Warning: Could not parse existing JSON file: {e}")
            print("Starting fresh...")
            existing_data = []
    
    return scraped_plans, existing_data

def format_json_compact_history(data):
    """Format JSON with history arrays compressed to single line."""
    json_str = json.dumps(data, ensure_ascii=False, indent=4)
    
    # Compress history arrays to single line
    import re
    
    def find_matching_bracket(text, start_pos):
        """Find the matching closing bracket for an opening bracket."""
        depth = 0
        i = start_pos
        while i < len(text):
            if text[i] == '[':
                depth += 1
            elif text[i] == ']':
                depth -= 1
                if depth == 0:
                    return i
            i += 1
        return -1
    
    # Find all "history" fields and compress them
    pattern = r'(\s+)"history":\s*\['
    matches = list(re.finditer(pattern, json_str))
    
    # Process matches in reverse order to avoid index shifting
    for match in reversed(matches):
        start_pos = match.end() - 1  # Position of opening [
        end_pos = find_matching_bracket(json_str, start_pos)
        
        if end_pos != -1:
            indent_spaces = match.group(1)
            # Extract the entire array content
            array_content = json_str[start_pos + 1:end_pos]
            
            # Remove all newlines and extra whitespace, but preserve structure
            compressed = re.sub(r'\s+', ' ', array_content).strip()
            # Clean up spacing around brackets and commas
            compressed = re.sub(r'\s*\[\s*', '[', compressed)
            compressed = re.sub(r'\s*\]\s*', ']', compressed)
            compressed = re.sub(r'\s*,\s*', ', ', compressed)
            
            # Replace the entire history array with compact version
            json_str = json_str[:match.start()] + f'{indent_spaces}"history": [{compressed}]' + json_str[end_pos + 1:]
    
    return json_str

def main():
    input_csv = 'bat_yam_taba_list.csv'
    output_json = 'bat_yam_plans_data.json' # שינוי סיומת ל-json רגיל
    
    print(f"Reading CSV file: {input_csv}...")
    try:
        df = pd.read_csv(input_csv)
    except FileNotFoundError:
        print("Error: The file 'bat_yam_taba_list.csv' was not found.")
        return

    # Load existing scraped plans
    scraped_plans, existing_data = load_existing_plans(output_json)
    
    # Filter out already scraped plans
    df['already_scraped'] = df['Taba_Number'].astype(str).isin(scraped_plans)
    df_to_scrape = df[~df['already_scraped']].copy()
    
    total_rows = len(df)
    remaining_rows = len(df_to_scrape)
    
    if remaining_rows == 0:
        print(f"All {total_rows} plans have already been scraped. Nothing to do!")
        return
    
    print(f"Found {total_rows} total plans in CSV.")
    print(f"  - {len(scraped_plans)} already scraped")
    print(f"  - {remaining_rows} remaining to scrape")
    print(f"Saving incrementally to {output_json}...\n")

    # Start with existing data
    all_data = existing_data.copy()
    
    # פתיחת הקובץ לכתיבה (נכתוב הכל מחדש בסוף)
    temp_data = []
    
    for index, row in df_to_scrape.iterrows():
        taba_number = row['Taba_Number']
        serial_id = row['Serial_ID']
        original_index = df.index.get_loc(index)
        
        print(f"[{original_index + 1}/{total_rows}] Scraping Plan: {taba_number} (ID: {serial_id})...")
        
        data = scrape_plan(serial_id, taba_number)
        
        if data:
            temp_data.append(data)
            all_data.append(data)
            
            # Save incrementally every 10 entries
            if len(temp_data) >= 10:
                with open(output_json, 'w', encoding='utf-8') as f:
                    f.write(format_json_compact_history(all_data))
                temp_data = []
                print(f"  -> Progress saved ({len(all_data)}/{total_rows} total)")
        
        time.sleep(0.5)
    
    # Final save
    with open(output_json, 'w', encoding='utf-8') as f:
        f.write(format_json_compact_history(all_data))
    
    print(f"\nDone! Scraped {remaining_rows} new plans. Total plans in file: {len(all_data)}")

if __name__ == "__main__":
    main()