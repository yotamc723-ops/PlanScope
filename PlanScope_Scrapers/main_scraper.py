import os
import sys
import subprocess
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional

# --- Configuration ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DAILY_REPORTS_DIR = os.path.join(BASE_DIR, "daily_reports")

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(BASE_DIR, "main_scraper.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("MainScraper")

def run_scraper(script_rel_path: str, cwd_rel_path: str, scraper_name: str) -> bool:
    """
    Runs a scraper script via subprocess.
    """
    script_path = os.path.join(BASE_DIR, script_rel_path)
    cwd_path = os.path.join(BASE_DIR, cwd_rel_path)
    
    logger.info(f"▶️ Starting {scraper_name} Scraper...")
    try:
        # Use sys.executable to ensure we use the same python interpreter
        cmd = [sys.executable, script_path]
        result = subprocess.run(cmd, cwd=cwd_path, check=True, capture_output=False)
        logger.info(f"✅ {scraper_name} finished successfully.")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ {scraper_name} failed with exit code {e.returncode}.")
        return False
    except Exception as e:
        logger.error(f"❌ {scraper_name} failed with error: {e}")
        return False

def load_json_file(filepath: str) -> Optional[Dict[str, Any]]:
    """Loads a JSON file safely."""
    if not os.path.exists(filepath):
        logger.warning(f"File not found: {filepath}")
        return None
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading {filepath}: {e}")
        return None

def main():
    start_time = datetime.now()
    logger.info(f"🚀 Starting Global PlanScope Scraper at {start_time}")
    
    # Ensure output dir exists
    if not os.path.exists(DAILY_REPORTS_DIR):
        os.makedirs(DAILY_REPORTS_DIR)

    # Parse args
    merge_only = "--merge-only" in sys.argv

    # 1. Execute Scrapers
    taba_success = True
    permits_success = True
    yeshivot_success = True

    if not merge_only:
        # Taba
        taba_success = run_scraper(
            script_rel_path="taba/main_taba.py",
            cwd_rel_path="taba",
            scraper_name="Taba"
        )
        
        # Permits
        permits_success = run_scraper(
            script_rel_path="permits/main_permit.py",
            cwd_rel_path="permits",
            scraper_name="Permits"
        )
        
        # Yeshivot
        yeshivot_success = run_scraper(
            script_rel_path="yeshivot/daily_yeshivot_scanner.py",
            cwd_rel_path="yeshivot",
            scraper_name="Yeshivot"
        )
    else:
        logger.info("⚠️ Running in MERGE-ONLY mode. Skipping scraper execution.")

    # 2. Collect & Merge Reports
    logger.info("🔄 collecting and merging daily reports...")
    
    today = datetime.now()
    # Date formats
    date_taba = today.strftime("%Y%m%d")      # YYYYMMDD
    date_permits = today.strftime("%Y_%m_%d") # YYYY_MM_DD
    date_yeshivot = today.strftime("%Y-%m-%d") # YYYY-MM-DD
    
    # Define paths
    taba_report_path = os.path.join(BASE_DIR, "taba", "diff", f"daily_report_{date_taba}.json")
    permits_report_path = os.path.join(BASE_DIR, "permits", "diff", f"permit_daily_report_{date_permits}.json")
    yeshivot_report_path = os.path.join(BASE_DIR, "yeshivot", "processed_json", f"daily_report_{date_yeshivot}.json")
    
    # Load data
    taba_data = load_json_file(taba_report_path)
    permits_data = load_json_file(permits_report_path)
    yeshivot_data = load_json_file(yeshivot_report_path)
    
    # Construct Unified Report
    unified_report = {
        "date": date_yeshivot, # Standard ISO-like
        "generated_at": datetime.now().isoformat(),
        "status": {
            "taba": "success" if taba_success and taba_data else "failed/missing",
            "permits": "success" if permits_success and permits_data else "failed/missing",
            "yeshivot": "success" if yeshivot_success and yeshivot_data else "failed/missing"
        },
        "data": {
            "taba": taba_data,
            "permits": permits_data,
            "yeshivot": yeshivot_data
        }
    }
    
    # Save Unified Report
    output_filename = f"unified_daily_report_{date_permits}.json"
    output_path = os.path.join(DAILY_REPORTS_DIR, output_filename)
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(unified_report, f, indent=4, ensure_ascii=False)
        logger.info(f"✅ Unified report saved successfully: {output_path}")
    except Exception as e:
        logger.error(f"❌ Failed to save unified report: {e}")

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"🏁 Global Scraper finished in {duration}")

if __name__ == "__main__":
    main()
