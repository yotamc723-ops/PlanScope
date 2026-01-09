import csv
import json
import os
import re
import time
import pdfplumber
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from typing import List, Dict, Any

# טעינת קובץ .env מהתיקייה הראשית
root_dir = Path(__file__).parent.parent.parent
load_dotenv(root_dir / '.env')

# --- הגדרות ---
INPUT_CSV = "meeting_index.csv"
PDF_DIR = "decision_protocols"
OUTPUT_DIR = "processed_json"
TEXT_DIR = "processed_texts"
UNIFIED_JSON_NAME = "all_meetings_data.json"

# הגדרת הלקוח של OpenAI
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# הוראות המערכת (System Prompt) - הגדרות "יבשות" ומדויקות
SYSTEM_INSTRUCTION = """
You are an expert real estate analyst specializing in Israeli municipal protocols (Bat Yam).
Your task is to analyze construction permit applications and decisions, extracting ONLY those that represent significant real estate investment or development opportunities.

PART 1: IDENTIFICATION & CLASSIFICATION

You will encounter two distinct types of items. You must output a specific JSON structure for each.

TYPE A: PLANNING SCHEMES (נושאים תכנוניים / תב"ע / תמ"ל)

Identification: IDs with hyphens/slashes (e.g., "502-0654321", "תמ/2035", "בי/xxxx"). Often at the start of the document.

Goal: Strategic analysis of zoning changes.

TYPE B: BUILDING PERMITS (בקשות להיתר)

Identification: Standard 8-digit IDs (e.g., 20250123).

Goal: Specific building project analysis.

PART 2: FILTERING RULES (CRITICAL)

KEEP the item ONLY if it matches one of the following precise definitions strictly.

תמ"א 38 (TAMA 38)
Definition: A National Outline Plan for the reinforcement of existing buildings against earthquakes (38/1 or 38/2).

הריסה / פינוי בינוי (Demolition / Pinui Binui)
Definition: Demolition of existing permanent buildings (residential or commercial, typically >2 floors) OR a full "Pinui Binui" process.

CRITICAL: Keep this item even if the request is ONLY for the demolition phase (without explicit mention of the new construction yet), as this signals the start of a significant project.

תכנית בניה עירונית - תב"ע (City Plan / Taba)
Definition: Statutory document regulating land use/building rights. Include only plans that change rights or designation.

תוכנית מתאר עירונית (Local Master Plan)
Definition: Comprehensive plan applying to the entire local authority or a significant district.

תוספת קומות (Addition of Floors)
Definition: Permit request for adding vertical levels to an existing building.

שדרוג תשתיות (Infrastructure Upgrade)
Definition: Major public engineering projects (Metro, Light Rail, roads, public buildings).

בקשות משמעותיות בפרויקטים גדולים (Major Project Updates)
Definition: Technical requests (such as "Splitting a Permit", Adding/Subtracting  stuff to the majority/all of the apartments in the project (balconies, area, etc.), "Renewing a Permit", "Change of Layout", "Excavation & Shoring" (חפירה ודיפון), "Demolition" (הריסה)) ONLY IF they refer to a "Mega-Project" (High-rise buildings, projects with >20 units, or commercial centers > 1000 sqm). Even if the request is technical, the scale makes it significant.

DISCARD (IGNORE) any request that represents minor, non-value-adding work, such as:

Balcony closures, Pergolas, Winter closures - only if its small and talks about less than 2 apartments.

Signage, Fences, Gates.

Minor repairs, Internal changes (unless for a Mega-Project as defined above).

Elevators in existing buildings.

Private house minor additions.

Single apartment additions.

NOTE: Do NOT discard requests for Total Demolition of an independent building, even if it looks like a "small" request.

PART 3: OUTPUT FORMAT (JSON)

CRITICAL LANGUAGE INSTRUCTION:
All output values (summaries, descriptions, categories) MUST BE IN HEBREW.
Only the JSON keys (e.g., "plan_number", "decision_status") remain in English.

Return a JSON object with a single list "decisions". The list can contain mixed objects (Type A and Type B).

SCHEMA FOR TYPE A (PLANNING SCHEME):

{
"type": "תב״ע",
"plan_number": "string (The Plan ID, e.g. '502-1234567')",
"project_category": "string (Always 'תכנית מתאר')",
"decision_stage": "string (e.g. 'הפקדה', 'מתן תוקף', 'דיון בהתנגדויות')",
"project_summary": "string (HEBREW: Short explanation of the plan's goal. If unclear, null)",
"decision_summary": "string (HEBREW: Concise summary of the decision for an investor)",
"changes_description": "string (HEBREW: What is changing? e.g. 'שינוי ייעוד מתעשייה למגורים, תוספת 500 יח"ד')",
"relevant_addresses": 

$$"string", "string"$$

,
"blocks_and_parcels": 

$$"string (STRICT FORMAT: 'gush,helka'. Ranges: 'gush,helka-helka'. Multiple helkas: 'gush,helka,helka'. Separate different Gushim with ';')"$$


}

SCHEMA FOR TYPE B (BUILDING PERMIT):

{
"type": "היתר בניה",
"request_id": "string (Request Number)",
"address": "string",
"applicant": "string",
"project_category": "string (One of the 7 Hebrew domains listed above in definitions)",
"essence": "string (The original Hebrew description)",
"decision_status": "string (Enum: 'אושר', 'אושר בתנאים', 'נדחה', 'נדחה במתכונת נוכחית בלבד')",
"units_added": int
}

Return ONLY valid JSON.
"""

# --- פונקציות עזר לעיבוד טקסט ---

def fix_hebrew_text(text):
    if not text: return ""
    # זיהוי חלקים שאינם עברית (אנגלית, מספרים, סימנים) והיפוך העברית בלבד
    parts = re.split(r'([a-zA-Z0-9\.\-\/:]+)', text)
    fixed_parts = []
    for part in parts:
        if re.search(r'[a-zA-Z0-9]', part):
            fixed_parts.append(part)
        else:
            fixed_parts.append(part[::-1])
    return "".join(fixed_parts[::-1])

def repair_broken_hebrew(text):
    if not text: return ""
    text = re.sub(r'\s*-\s*', '-', text)
    # תיקון אותיות סופיות וחיבור מילים שבורות - בסיסי
    text = re.sub(r'([\u0590-\u05FF]{2,})\s+([\u0590-\u05FF])(?!\w)', r'\1\2', text)
    text = re.sub(r'(?<!\w)([\u0590-\u05FF])\s+([\u0590-\u05FF]{2,})', r'\1\2', text)
    for _ in range(3):
        text = re.sub(r'\b([\u0590-\u05FF])\s+([\u0590-\u05FF])\b', r'\1\2', text)
    return text

def extract_text_from_pdf(pdf_path):
    """חילוץ טקסט מלא מקובץ PDF עם תיקוני עברית"""
    full_text = []
    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text(x_tolerance=5)
                if text:
                    lines = text.split('\n')
                    for line in lines:
                        fixed = fix_hebrew_text(line)
                        repaired = repair_broken_hebrew(fixed)
                        full_text.append(repaired)
        return "\n".join(full_text)
    except Exception as e:
        print(f"Error reading PDF {pdf_path}: {e}")
        return ""

def load_existing_data():
    """טוען נתונים קיימים מקובץ ה-JSON אם הוא קיים"""
    output_path = os.path.join(OUTPUT_DIR, UNIFIED_JSON_NAME)
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                return content.get("meetings", [])
        except Exception as e:
            print(f"Warning: Could not load existing JSON ({e}). Starting fresh.")
    return []

def save_unified_json(data):
    """שומר את כל המידע לקובץ JSON אחד באופן אטומי"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    output_path = os.path.join(OUTPUT_DIR, UNIFIED_JSON_NAME)
    final_output = {"meetings": data}
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(final_output, f, ensure_ascii=False, indent=4)
        print(f"   -> Successfully saved unified data to {output_path}")
    except Exception as e:
        print(f"Error saving unified JSON: {e}")

# --- לוגיקה ראשית ---

def process_row(row):
    meeting_num = row['Meeting Number']
    date = row['Date']
    local_filename = row['Local Filename']
    original_link = row['Original Link']
    
    pdf_path = os.path.join(PDF_DIR, local_filename)
    
    if not os.path.exists(pdf_path):
        print(f"Skipping {meeting_num}: File {local_filename} not found.")
        return None
    
    print(f"Processing Meeting {meeting_num} (Date: {date})...")
    
    # 1. חילוץ טקסט
    raw_text = extract_text_from_pdf(pdf_path)
    if not raw_text or len(raw_text) < 50:
        print("Text extraction failed or empty.")
        return None

    # שמירת טקסט לבקרה
    if not os.path.exists(TEXT_DIR):
        os.makedirs(TEXT_DIR)
    txt_filename = local_filename.rsplit('.', 1)[0] + ".txt"
    try:
        with open(os.path.join(TEXT_DIR, txt_filename), "w", encoding="utf-8") as f:
            f.write(raw_text)
    except Exception:
        pass

    # 2. שליחה ל-LLM
    try:
        user_prompt = f"Analyze the following protocol text and extract decisions:\n\n{raw_text[:30000]}"
        
        response = client.chat.completions.create(
            model="gpt-5-mini",
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        content = response.choices[0].message.content
        llm_data = json.loads(content)
        decisions_list = llm_data.get("decisions", [])
        
    except Exception as e:
        print(f"LLM Error for {meeting_num}: {e}")
        decisions_list = []

    # 3. החזרת המידע רק אם נמצאו החלטות רלוונטיות
    if not decisions_list:
        print(f"   -> No relevant investment opportunities found in {meeting_num}.")
        return None

    print(f"   -> Found {len(decisions_list)} relevant opportunities.")
    
    return {
        "metadata": {
            "meeting_id": meeting_num,
            "meeting_type": row.get('Meeting Type', ''),
            "meeting_date": date,
            "document_url": row.get('PDF Download URL', ''),
            "original_system_url": original_link,
            "local_file": local_filename
        },
        "decisions": decisions_list
    }

def main():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
    
    if not os.path.exists(INPUT_CSV):
        print("CSV file not found.")
        return

    # טעינת נתונים שכבר קיימים כדי לא לעבד מחדש
    all_meetings_data = load_existing_data()
    
    # שינוי: יצירת מפתח ייחודי המורכב מ-(מספר ישיבה, תאריך)
    processed_keys = {(m['metadata']['meeting_id'], m['metadata']['meeting_date']) for m in all_meetings_data}
    
    print(f"Found {len(all_meetings_data)} meetings already processed. Continuing...")
    
    with open(INPUT_CSV, mode='r', encoding='utf-8-sig') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            meeting_id = row['Meeting Number']
            date = row['Date']
            
            # דילוג רק אם גם המספר וגם התאריך כבר קיימים במאגר
            if (meeting_id, date) in processed_keys:
                continue
                
            result = process_row(row)
            
            if result:
                all_meetings_data.append(result)
                processed_keys.add((meeting_id, date))
                # שמירה לאחר כל ישיבה מוצלחת
                save_unified_json(all_meetings_data)
                time.sleep(1)

    print(f"\nProcessing complete. Total meetings in unified JSON: {len(all_meetings_data)}")

if __name__ == "__main__":
    main()