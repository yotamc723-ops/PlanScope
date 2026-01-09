import json
import os
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple

def load_json(filepath: str) -> List[Dict]:
    """טעינת קובץ JSON בצורה בטוחה"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading {filepath}: {e}")
        return []


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PLANS_DATA_DIR = os.path.join(BASE_DIR, "plans_data")
DIFF_DIR = os.path.join(BASE_DIR, "diff")

def get_latest_two_files(directory: str = PLANS_DATA_DIR, pattern: str = r"bat_yam_plans_data_(\d{4}_\d{2}_\d{2})\.json") -> Tuple[str, str]:
    """
    סורק את התיקייה ומוצא את שני הקבצים הכי עדכניים לפי התאריך בשם הקובץ.
    מחזיר (קובץ_חדש, קובץ_ישן)
    """
    if not os.path.exists(directory):
        print(f"Directory not found: {directory}")
        return None, None
        
    files = []
    for filename in os.listdir(directory):
        match = re.search(pattern, filename)
        if match:
            # הופך את התאריך לאובייקט datetime כדי שנוכל למיין בקלות
            date_str = match.group(1)
            date_obj = datetime.strptime(date_str, "%Y_%m_%d")
            files.append((date_obj, os.path.join(directory, filename)))
    
    # מיון לפי תאריך (מהישן לחדש)
    files.sort(key=lambda x: x[0])
    
    if len(files) < 2:
        return None, None
    
    # הקובץ האחרון הוא הכי חדש (היום), זה שלפניו הוא אתמול
    latest_file = files[-1][1]
    previous_file = files[-2][1]
    
    return latest_file, previous_file

def compare_plans(old_plans: List[Dict], new_plans: List[Dict]) -> Dict[str, Any]:
    """
    השוואה בין שתי רשימות של תוכניות ויצירת דו"ח שינויים.
    """
    old_map = {p['plan_number']: p for p in old_plans if 'plan_number' in p and p.get('status') != 'failed'}
    
    report = {
        "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "summary": {
            "total_plans_scanned": len([p for p in new_plans if p.get('status') != 'failed']),
            "new_plans_discovered": 0,
            "status_changes": 0,
            "new_history_events": 0,
            "new_meetings": 0
        },
        "changes": []
    }

    for new_plan in new_plans:
        # Skip failed scrapes
        if new_plan.get('status') == 'failed':
            continue

        plan_num = new_plan.get('plan_number')
        
        if plan_num not in old_map:
            report['changes'].append({
                "type": "NEW_PLAN",
                "plan_number": plan_num,
                "plan_name": new_plan.get('plan_name'),
                "details": "תוכנית חדשה נכנסה למאגר"
            })
            report['summary']['new_plans_discovered'] += 1
            continue

        old_plan = old_map[plan_num]
        plan_changes = {
            "type": "UPDATE",
            "plan_number": plan_num,
            "plan_name": new_plan.get('plan_name'),
            "updates": []
        }

        # השוואת סטטוס
        new_status = new_plan.get('general_info', {}).get('status')
        old_status = old_plan.get('general_info', {}).get('status')
        if new_status != old_status:
            plan_changes['updates'].append({
                "field": "status",
                "old_value": old_status,
                "new_value": new_status,
                "alert_level": "HIGH"
            })
            report['summary']['status_changes'] += 1

        # השוואת היסטוריה
        old_history_list = old_plan.get('history', [])
        new_history_list = new_plan.get('history', [])
        
        # Safe access to old latest description
        old_latest_desc = old_history_list[0][1] if old_history_list and len(old_history_list[0]) > 1 else None

        old_hist_set = set(tuple(x) for x in old_history_list)
        
        # Iterate through NEW history to find added items (preserving order)
        for item in new_history_list:
            item_tuple = tuple(item)
            if item_tuple not in old_hist_set:
                plan_changes['updates'].append({
                    "field": "history",
                    "date": item[0],
                    "description": item[1],
                    "new_description": item[1],
                    "old_description": old_latest_desc,
                    "alert_level": "MEDIUM"
                })
                report['summary']['new_history_events'] += 1

        # השוואת ישיבות
        def get_m_key(m): return f"{m.get('meeting_number')}-{m.get('meeting_date')}"
        new_meetings = {get_m_key(m): m for m in new_plan.get('meeting_history', [])}
        old_meetings = {get_m_key(m): m for m in old_plan.get('meeting_history', [])}

        for key, meeting in new_meetings.items():
            if key not in old_meetings:
                plan_changes['updates'].append({
                    "field": "meeting",
                    "date": meeting.get('meeting_date'),
                    "type": meeting.get('meeting_type'),
                    "link": meeting.get('meeting_link'),
                    "alert_level": "CRITICAL"
                })
                report['summary']['new_meetings'] += 1

        if plan_changes['updates']:
            report['changes'].append(plan_changes)

    return report

def main():
    print("🔍 Searching for plan data files...")
    latest_file, previous_file = get_latest_two_files()
    
    if not latest_file or not previous_file:
        print("❌ Could not find at least two files to compare.")
        print("Make sure your files follow the name format: bat_yam_plans_data_YYYY_MM_DD.json")
        return

    print(f"📅 Comparing NEW: {latest_file} VS OLD: {previous_file}")
    
    new_data = load_json(latest_file)
    old_data = load_json(previous_file)
    
    if not new_data or not old_data:
        print("❌ One of the files is empty or corrupted.")
        return

    report = compare_plans(old_data, new_data)
    
    
    # שמירת הדו"ח
    if not os.path.exists(DIFF_DIR):
        os.makedirs(DIFF_DIR)
        
    report_filename = os.path.join(DIFF_DIR, f"daily_report_{datetime.now().strftime('%Y%m%d')}.json")
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=4, ensure_ascii=False)
        
    print(f"✅ Report generated successfully: {report_filename}")
    print(f"🚀 Found {len(report['changes'])} plans with updates.")

if __name__ == "__main__":
    main()