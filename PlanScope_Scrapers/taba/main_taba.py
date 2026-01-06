import os
import shutil
import subprocess
import logging
import sys
from datetime import datetime
import glob
from typing import List

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("daily_orchestrator_taba.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("OrchestratorTaba")

TABA_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(TABA_DIR, ".backup")

# Critical Status Files to Backup/Restore
CRITICAL_FILES = [
    "bat_yam_taba_list.csv"
]

# Scripts to Run Sequence
SCRIPTS = [
    "get_taba_id.py",
    "get_information_taba.py",
    "daily_report_generator_taba.py"
]

class BackupManager:
    """Handles backup and restoration of critical files."""
    
    def __init__(self):
        self.backed_up_files = []

    def __enter__(self):
        self.create_backup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            logger.error(f"Error detected: {exc_val}")
            self.restore_backup()
        else:
            self.cleanup_backup()

    def create_backup(self):
        """Copies critical files to backup dir."""
        logger.info("📦 Creating system backup...")
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        for filename in CRITICAL_FILES:
            src = os.path.join(TABA_DIR, filename)
            if os.path.exists(src):
                dst = os.path.join(BACKUP_DIR, filename)
                shutil.copy2(src, dst)
                self.backed_up_files.append(filename)
                logger.debug(f"Backed up: {filename}")
            else:
                logger.warning(f"File not found for backup: {filename}")

    def restore_backup(self):
        """Restores files from backup dir and cleans up new junk."""
        logger.warning("⚠️ Restoring system state from backup...")
        for filename in self.backed_up_files:
            src = os.path.join(BACKUP_DIR, filename)
            dst = os.path.join(TABA_DIR, filename)
            shutil.copy2(src, dst)
            logger.info(f"Restored: {filename}")
        
        self.cleanup_new_files()

    def cleanup_new_files(self):
        """Deletes files created during the failed run to keep directory clean."""
        now = datetime.now()
        today_date = now.strftime("%Y_%m_%d")
        compact_date = now.strftime("%Y%m%d")
        
        patterns = [
            f"bat_yam_plans_data_{today_date}.json",
            f"bat_yam_plans_data_{today_date}.jsonl",
            f"daily_report_{compact_date}.json"
        ]
        
        for pattern in patterns:
            file_path = os.path.join(TABA_DIR, pattern)
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🗑️ Deleted partial/failed output: {pattern}")

    def cleanup_backup(self):
        """Deletes the backup folder on success."""
        logger.info("✅ Pipeline successful. Removing backups.")
        if os.path.exists(BACKUP_DIR):
            shutil.rmtree(BACKUP_DIR)


def run_pipeline():
    start_time = datetime.now()
    logger.info(f"🚀 Starting Main Taba Orchestrator at {start_time}")
    
    with BackupManager():
        for script in SCRIPTS:
            script_path = os.path.join(TABA_DIR, script)
            logger.info(f"▶️ Running: {script}...")
            
            try:
                # Use sys.executable to ensure we use the same python interpreter (important for venv)
                cmd = [sys.executable, script_path] 
                result = subprocess.run(cmd, check=True, cwd=TABA_DIR, capture_output=False)
                
            except subprocess.CalledProcessError as e:
                logger.error(f"❌ Script failed: {script} (Exit Code: {e.returncode})")
                raise e # Trigger __exit__ rollback

    end_time = datetime.now()
    duration = end_time - start_time
    logger.info(f"🏁 Orchestrator finished successfully in {duration}")

if __name__ == "__main__":
    try:
        run_pipeline()
    except Exception as e:
        logger.critical(f"🛑 Pipeline aborted due to error: {e}")
        exit(1)
