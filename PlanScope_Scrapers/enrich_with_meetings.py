"""
Enrich Permits & Plans with Meeting History

This script cross-references permits and plans with municipal meeting discussions,
creating enriched JSON files with complete decision history.

Input Files:
- permits/opportunities.json (permits data)
- taba/bat_yam_plans_data.json (plans data)
- yeshivot/processed_json/all_meetings_data.json (meeting discussions)

Output Files:
- permit_full.json (enriched permits)
- plans_full.json (enriched plans)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# File paths
SCRIPT_DIR = Path(__file__).parent
PERMITS_FILE = SCRIPT_DIR / "permits" / "opportunities.json"
PLANS_FILE = SCRIPT_DIR / "taba" / "bat_yam_plans_data.json"
MEETINGS_FILE = SCRIPT_DIR / "yeshivot" / "processed_json" / "all_meetings_data.json"
OUTPUT_PERMITS_FILE = SCRIPT_DIR / "permit_full.json"
OUTPUT_PLANS_FILE = SCRIPT_DIR / "plans_full.json"


def load_json(file_path: Path) -> Any:
    """Load JSON file and return parsed data."""
    print(f"Loading {file_path.name}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def parse_date(date_str: str) -> tuple:
    """Parse date string to tuple for sorting (day, month, year)."""
    try:
        # Handle format: DD/MM/YYYY
        parts = date_str.split('/')
        if len(parts) == 3:
            return (int(parts[2]), int(parts[1]), int(parts[0]))  # (year, month, day)
    except:
        pass
    return (0, 0, 0)  # Default for unparseable dates


def build_permit_meeting_index(meetings_data: Dict) -> Dict[str, List[Dict]]:
    """
    Build an index mapping permit_id to list of meeting discussions.
    
    Returns:
        Dict mapping permit_id -> [list of meeting history entries]
    """
    print("\nBuilding permit-meeting index...")
    permit_index = {}
    
    for meeting in meetings_data.get("meetings", []):
        meeting_id = meeting["metadata"]["meeting_id"]
        meeting_date = meeting["metadata"]["meeting_date"]
        
        for decision in meeting.get("decisions", []):
            # Only process BUILDING_PERMIT decisions
            if decision.get("type") == "BUILDING_PERMIT":
                request_id = decision.get("request_id")
                
                if request_id:
                    # Create meeting history entry
                    history_entry = {
                        "meeting_id": meeting_id,
                        "meeting_date": meeting_date,
                        "essence": decision.get("essence"),
                        "decision_status": decision.get("decision_status")
                    }
                    
                    # Add to index
                    if request_id not in permit_index:
                        permit_index[request_id] = []
                    permit_index[request_id].append(history_entry)
    
    print(f"  Found {len(permit_index)} unique permits discussed in meetings")
    return permit_index


def build_plan_meeting_index(meetings_data: Dict) -> Dict[str, List[Dict]]:
    """
    Build an index mapping plan_number to list of meeting discussions.
    
    Returns:
        Dict mapping plan_number -> [list of meeting history entries]
    """
    print("\nBuilding plan-meeting index...")
    plan_index = {}
    
    for meeting in meetings_data.get("meetings", []):
        meeting_id = meeting["metadata"]["meeting_id"]
        meeting_date = meeting["metadata"]["meeting_date"]
        
        for decision in meeting.get("decisions", []):
            # Only process PLANNING_SCHEME decisions
            if decision.get("type") == "PLANNING_SCHEME":
                plan_number = decision.get("plan_number")
                
                if plan_number:
                    # Create meeting history entry
                    history_entry = {
                        "meeting_id": meeting_id,
                        "meeting_date": meeting_date,
                        "decision_stage": decision.get("decision_stage"),
                        "decision_summary": decision.get("decision_summary"),
                        "changes_description": decision.get("changes_description")
                    }
                    
                    # Add to index
                    if plan_number not in plan_index:
                        plan_index[plan_number] = []
                    plan_index[plan_number].append(history_entry)
    
    print(f"  Found {len(plan_index)} unique plans discussed in meetings")
    return plan_index


def enrich_permits(permits_data: List[Dict], permit_index: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Enrich permits data with meeting history.
    
    Args:
        permits_data: List of permit objects
        permit_index: Index mapping permit_id to meeting history
        
    Returns:
        Enriched list of permits with meeting_history field
    """
    print("\nEnriching permits with meeting history...")
    enriched_permits = []
    matches_found = 0
    
    for permit in permits_data:
        # Create enriched copy
        enriched = permit.copy()
        permit_id = permit.get("permit_id")
        
        # Look up meeting history
        if permit_id and permit_id in permit_index:
            meeting_history = permit_index[permit_id]
            # Sort by date (chronologically)
            meeting_history.sort(key=lambda x: parse_date(x["meeting_date"]))
            enriched["meeting_history"] = meeting_history
            matches_found += 1
        else:
            enriched["meeting_history"] = []
        
        enriched_permits.append(enriched)
    
    print(f"  Processed {len(enriched_permits)} permits")
    print(f"  Found meeting history for {matches_found} permits ({matches_found/len(enriched_permits)*100:.1f}%)")
    return enriched_permits


def enrich_plans(plans_data: List[Dict], plan_index: Dict[str, List[Dict]]) -> List[Dict]:
    """
    Enrich plans data with meeting history.
    
    Args:
        plans_data: List of plan objects
        plan_index: Index mapping plan_number to meeting history
        
    Returns:
        Enriched list of plans with meeting_history field
    """
    print("\nEnriching plans with meeting history...")
    enriched_plans = []
    matches_found = 0
    
    for plan in plans_data:
        # Create enriched copy
        enriched = plan.copy()
        plan_number = plan.get("plan_number")
        
        # Look up meeting history
        if plan_number and plan_number in plan_index:
            meeting_history = plan_index[plan_number]
            # Sort by date (chronologically)
            meeting_history.sort(key=lambda x: parse_date(x["meeting_date"]))
            enriched["meeting_history"] = meeting_history
            matches_found += 1
        else:
            enriched["meeting_history"] = []
        
        enriched_plans.append(enriched)
    
    print(f"  Processed {len(enriched_plans)} plans")
    print(f"  Found meeting history for {matches_found} plans ({matches_found/len(enriched_plans)*100:.1f}%)")
    return enriched_plans


def save_json(data: Any, file_path: Path):
    """Save data to JSON file with proper formatting."""
    print(f"\nSaving {file_path.name}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # Get file size
    size_mb = file_path.stat().st_size / (1024 * 1024)
    print(f"  Saved: {file_path}")
    print(f"  Size: {size_mb:.2f} MB")


def main():
    """Main enrichment workflow."""
    print("=" * 70)
    print("Enrich Permits & Plans with Meeting History")
    print("=" * 70)
    
    # Load all input files
    permits_data = load_json(PERMITS_FILE)
    plans_data = load_json(PLANS_FILE)
    meetings_data = load_json(MEETINGS_FILE)
    
    print(f"\nLoaded:")
    print(f"  - {len(permits_data)} permits")
    print(f"  - {len(plans_data)} plans")
    print(f"  - {len(meetings_data.get('meetings', []))} meetings")
    
    # Build indexes for fast lookups
    permit_index = build_permit_meeting_index(meetings_data)
    plan_index = build_plan_meeting_index(meetings_data)
    
    # Enrich permits and plans
    enriched_permits = enrich_permits(permits_data, permit_index)
    enriched_plans = enrich_plans(plans_data, plan_index)
    
    # Save enriched data
    save_json(enriched_permits, OUTPUT_PERMITS_FILE)
    save_json(enriched_plans, OUTPUT_PLANS_FILE)
    
    print("\n" + "=" * 70)
    print("Enrichment Complete!")
    print("=" * 70)
    print(f"\nOutput files:")
    print(f"  - {OUTPUT_PERMITS_FILE}")
    print(f"  - {OUTPUT_PLANS_FILE}")


if __name__ == "__main__":
    main()

