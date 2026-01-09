import json
import glob
import os
import sys
from datetime import datetime
from typing import Dict, List, Any, Optional


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PERMITS_DATA_DIR = os.path.join(BASE_DIR, "permits_data")
DIFF_DIR = os.path.join(BASE_DIR, "diff")
REPORT_PREFIX = "permit_daily_report_"
DATA_PREFIX = "bat_yam_permits_data_"

def load_json(filepath: str) -> Dict[str, Any]:
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    # Convert list to dict keyed by permit_id for easier lookup
    return {item['permit_id']: item for item in data if 'permit_id' in item}

def get_latest_two_files(directory: str, prefix: str) -> List[str]:
    files = glob.glob(os.path.join(directory, f"{prefix}*.json"))
    # Sort by filename (which includes date YYYY_MM_DD) descending
    files.sort(reverse=True)
    return files[:2]

def extract_date_from_filename(filename: str) -> str:
    # Expected format: bat_yam_permits_data_2026_01_06.json
    basename = os.path.basename(filename)
    # Remove prefix and extension
    date_part = basename.replace(DATA_PREFIX, "").replace(".json", "")
    return date_part

def compare_permits(new_permits: Dict[str, Any], old_permits: Dict[str, Any]) -> Dict[str, Any]:
    report = {}

    for permit_id, new_data in new_permits.items():
        if permit_id not in old_permits:
            continue # Only comparing changeable keys on existing permits as per instruction

        old_data = old_permits[permit_id]
        changes = {}

        # 1. Compare Requirements Level
        new_req = new_data.get('requirements_level')
        old_req = old_data.get('requirements_level')

        # Normalize to lists (handle None or unexpected types gracefully)
        if new_req is None: new_req = []
        if old_req is None: old_req = []

        if new_req != old_req:
            # Requirements are lists of dicts: {"Phaze":..., "Requirement":..., "Date":..., "Status":...}
            
            # 1. Identify added items (present in new but not in old)
            # using explicit comparison since dicts are not hashable by default unless we convert
            added_items = [item for item in new_req if item not in old_req]
            
            if added_items:
                # 2. Determine if Phaze changed (Global flag)
                # Collect all phases from the old list
                old_phases = set(item.get('Phaze') for item in old_req if item.get('Phaze'))
                
                status_changed = "no"
                for item in added_items:
                    if item.get('Phaze') and item.get('Phaze') not in old_phases:
                        status_changed = "yes"
                        break
                
                # 3. Get the last item from the old list ("newest old")
                old_last = old_req[-1] if old_req else None
                
                changes['requirements_level'] = {
                    'old': old_last,
                    'new': added_items,
                    'status_changed': status_changed
                }

        # 2. Compare History (New logic: Newest old value + New additions)
        new_history = new_data.get('history', [])
        old_history = old_data.get('history', [])

        if new_history != old_history:
            history_change = {}
            
            # Get the top of the old history ("newest oldest value")
            previous_latest = old_history[0] if old_history else None
            
            # Find new events (those appearing before the previous_latest in the new list)
            new_events = []
            
            if previous_latest:
                # Try to find the previous latest event in the new history based on description and date
                # We match on description and date because status/end_date might change
                match_index = -1
                prev_key = (previous_latest.get('event_description'), previous_latest.get('event_date'))
                
                for i, event in enumerate(new_history):
                    curr_key = (event.get('event_description'), event.get('event_date'))
                    if curr_key == prev_key:
                        match_index = i
                        break
                
                if match_index != -1:
                    # All events before the match are new
                    new_events = new_history[:match_index]
                    # CAPTURE THE UPDATED VERSION OF THE PREVIOUS LATEST FROM THE NEW FILE
                    previous_latest = new_history[match_index]
                else:
                    # Could not match, possibly completely new history or major change
                    # Fallback: Just take the top new event or all?
                    # User asked for "the new one that just popped", let's give the top one if strictly tracking "latest"
                    # But safest is to return all if we lost track, or maybe just the first.
                    # Let's return the whole list if we can't align, to be safe, OR just the top.
                    # Given the "stack" nature, if we can't find the old top, maybe it was removed?
                    # Let's assume all current top ones are new.
                    new_events = new_history 
            else:
                # No old history, everything is new
                new_events = new_history

            # Only report if there are actual new events or if we want to show the transition
            # The user wants "newest oldest" and "new one that popped".
            # If new_events is empty but history changed (e.g. status change of the top item),
            # we should still report it?
            # Case: Old[0] became Closed (modified), no new insertion.
            # In that case new_events might be empty if we match by desc/date.
            # BUT, if the user considers a status change as "popping", we might want to show the modified top match?
            # User said: "new one that just popped". Usually implies addition.
            # If status changed, strictly speaking it's the SAME event, just updated.
            # But let's look at the example: New[0] was ADDED ("עודכנו פרטי..."). Old[0] was pushed to New[1] and updated.
            # So New[0] is the new one.
            
            # If nothing was added (just update to existing), new_events matching loop above yields empty list.
            # Let's ensure IF new_events is empty but the objects differ, we might want to flag the update?
            # For now, adhering to "new one that just popped" -> Additions.
            
            history_change['new_events'] = new_events
            if previous_latest:
                history_change['previous_latest'] = previous_latest
                
            changes['history'] = history_change

        # 3. Compare Meeting History (Mention only new meetings)
        new_meetings = new_data.get('meeting_history', [])
        old_meetings = old_data.get('meeting_history', [])
        
        # Identify new meetings by meeting_id if available, or full object equality
        # Assuming meeting_id is reliable.
        old_meeting_ids = {m.get('meeting_id') for m in old_meetings if m.get('meeting_id')}
        
        added_meetings = []
        for meeting in new_meetings:
            mid = meeting.get('meeting_id')
            if mid:
                if mid not in old_meeting_ids:
                    added_meetings.append(meeting)
            else:
                # Fallback if no ID: check if this exact object is in old list
                if meeting not in old_meetings:
                    added_meetings.append(meeting)
        
        if added_meetings:
            changes['meeting_history'] = added_meetings

        if changes:
            report[permit_id] = changes

    return report

def main():
    files = get_latest_two_files(PERMITS_DATA_DIR, DATA_PREFIX)
    
    if len(files) < 2:
        print("Not enough data files to compare. Need at least 2.")
        return

    new_file = files[0]
    old_file = files[1]
    
    print(f"Comparing newer file: {os.path.basename(new_file)}")
    print(f"With older file:      {os.path.basename(old_file)}")

    new_data = load_json(new_file)
    old_data = load_json(old_file)

    report_data = compare_permits(new_data, old_data)

    if report_data:
        date_str = extract_date_from_filename(new_file)
        report_filename = f"{REPORT_PREFIX}{date_str}.json"
        
        if not os.path.exists(DIFF_DIR):
            os.makedirs(DIFF_DIR)
            
        report_path = os.path.join(DIFF_DIR, report_filename)
        
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        print(f"Report generated: {report_filename}")
        print(f"Total permits with changes: {len(report_data)}")
    else:
        print("No changes found matching the criteria.")

if __name__ == "__main__":
    main()
