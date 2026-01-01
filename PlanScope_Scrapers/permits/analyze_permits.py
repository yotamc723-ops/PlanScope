"""
Stage 2 & 3: API Data Retrieval + AI Filtering Pipeline

This script reads permit IDs from permit_numbers.txt, fetches the "מהות הבקשה" 
(Request Intention) field from the Bat Yam API, and uses GPT-5-mini to identify
investor-relevant opportunities like Tama 38, Pinui Binui, and new developments.

Usage:
    1. Create .env file with: OPENAI_API_KEY=your-key-here
    2. pip install -r requirements.txt
    3. python analyze_permits.py
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from dotenv import load_dotenv

# ============================================================================
# CONFIGURATION
# ============================================================================

# Load environment variables from .env file
load_dotenv()

# API endpoint template
API_URL_TEMPLATE = (
    "https://handasi.complot.co.il/magicscripts/mgrqispi.dll"
    "?appname=cixpa&prgname=GetBakashaFile&siteid=81&b={permit_id}&arguments=siteid,b"
)

# Request headers to mimic browser
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
    'Referer': 'https://batyam.complot.co.il/',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'he-IL,he;q=0.9,en-US;q=0.8,en;q=0.7',
}

# Rate limiting configuration
REQUEST_DELAY_MIN = 2.0  # Minimum delay between requests (seconds)
REQUEST_DELAY_MAX = 5.0  # Maximum delay between requests (seconds)
BATCH_SIZE = 10          # Number of requests before cooldown
BATCH_COOLDOWN = 20      # Cooldown duration after batch (seconds)

# Request timeout (seconds)
REQUEST_TIMEOUT = 30

# Files
PERMIT_FILE = "permit_numbers.txt"
OUTPUT_FILE = "opportunities.json"
ERROR_LOG_FILE = "errors.log"
DEBUG_REQUESTS_FILE = "model_requests.txt"

# LLM System Prompt for investor opportunity analysis
SYSTEM_PROMPT = """You are a real estate investment analyst specializing in Israeli construction permits.

You will receive the "מהות הבקשה" (Request Intention) text from a Bat Yam building permit. Analyze it and determine if it represents a valuable investment opportunity.

RELEVANT OPPORTUNITIES include:
- תמ"א 38 (Tama 38) - earthquake reinforcement with added units
- פינוי בינוי (Pinui Binui) - demolition and reconstruction  
- הריסה ובנייה (Demolition and Construction)
- New residential projects with multiple units
- מגדל מגורים (Residential tower)
- Addition of floors or significant expansions
- Major renovations creating new residential units
- Mixed-use developments with residential components
- Big updrades to infrastructures, public transportation and enviromental bit upgrades.

NOT RELEVANT (ignore):
Treat as NOT relevant any permit that describes only small, non-value-adding work and does NOT include major construction/expansion or creation of new residential units.
Examples: balcony closure, pergola, signs, small repairs/minor renovations, interior-only changes, storage room, fence, AC/ventilation installations.


OUTPUT FORMAT (JSON only, no markdown, no code blocks):
{
  "is_relevant": true,
  "permit_id": "...",
  "project_type": "Tama 38 / Pinui Binui / New Construction / Mixed-Use / etc.",
  "description": "copy the Hebrew description text",
  "num_units": "number of residential units if mentioned (יח\"ד), otherwise null",
  "key_features": ["list", "key", "points"]
}

If NOT relevant:
{
  "is_relevant": false,
  "permit_id": "...",
  "reason": "brief explanation"
}"""

# ============================================================================
# LOGGING SETUP
# ============================================================================

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(ERROR_LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============================================================================
# FUNCTIONS
# ============================================================================

def _get_text(el) -> Optional[str]:
    """Return stripped text from a BeautifulSoup element, cleaned of control characters."""
    if not el:
        return None
    txt = el.get_text(separator=" ", strip=True)
    # Clean up invisible Unicode control characters (RLM U+200F, LRM U+200E)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None


def _parse_request_info(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    info_table = soup.select_one("#info-main table tbody")
    if not info_table:
        return {"request_type": None, "main_use": None}

    rows = info_table.select("tr")
    # Get the second td (index 1) which contains the value, not the label (first td)
    # Row 2 = סוג הבקשה (request type), Row 3 = שימוש עיקרי (main use)
    request_type = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    main_use = _get_text(rows[3].find_all("td")[1]) if len(rows) >= 4 and len(rows[3].find_all("td")) > 1 else None
    return {"request_type": request_type, "main_use": main_use}


def _parse_address(soup: BeautifulSoup) -> Optional[str]:
    # Address is in the 4th h5 element inside #navbar-titles-id
    # Structure: h5[0]=label, h5[1]=permit#, h5[2]=label "כתובת:", h5[3]=actual address
    navbar = soup.select_one("#navbar-titles-id")
    if navbar:
        h5_elements = navbar.find_all("h5")
        # Get the 4th h5 (index 3) which contains the address
        if len(h5_elements) >= 4:
            return _get_text(h5_elements[3])
    
    # Fallback: try col-md-4 div which contains address
    address = soup.select_one("#navbar-titles-id .col-md-4 h5")
    return _get_text(address)


def _parse_applicants(soup: BeautifulSoup) -> Dict[str, Optional[str]]:
    table = soup.select_one("#table-baaley-inyan table tbody")
    if not table:
        return {"requestor": None, "owner": None, "author": None}

    rows = table.select("tr")
    requestor = _get_text(rows[0].find_all("td")[1]) if len(rows) >= 1 and len(rows[0].find_all("td")) > 1 else None
    owner = _get_text(rows[1].find_all("td")[1]) if len(rows) >= 2 and len(rows[1].find_all("td")) > 1 else None
    author = _get_text(rows[2].find_all("td")[1]) if len(rows) >= 3 and len(rows[2].find_all("td")) > 1 else None
    return {"requestor": requestor, "owner": owner, "author": author}


def _parse_parcels(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    parcels = []
    table = soup.select_one("#table-gushim-helkot table tbody")
    if not table:
        return parcels

    for row in table.select("tr"):
        tds = row.find_all("td")
        # Structure: td[0]=empty/link, td[1]=gush, td[2]=helka
        if len(tds) >= 3:
            gush = _get_text(tds[1])
            helka = _get_text(tds[2])
            parcels.append({"gush": gush, "helka": helka})
    return parcels


def _parse_history(soup: BeautifulSoup) -> List[Dict[str, Optional[str]]]:
    history = []
    table = soup.select_one("#table-events table tbody")
    if not table:
        return history

    for row in table.select("tr"):
        tds = row.find_all("td")
        if not tds:
            continue
        event_type = _get_text(tds[0]) if len(tds) > 0 else None
        event_description = _get_text(tds[1]) if len(tds) > 1 else None
        event_date = _get_text(tds[2]) if len(tds) > 2 else None
        event_end_date = _get_text(tds[3]) if len(tds) > 3 else None
        history.append({
            "event_type": event_type,
            "event_description": event_description,
            "event_date": event_date,
            "event_end_date": event_end_date,
        })
    return history


def fetch_permit_data(permit_id: str, max_retries: int = 2) -> Tuple[Optional[str], Dict[str, Any]]:
    """
    Fetch HTML from API and extract:
      - "מהות הבקשה" text (mahut_text)
      - request type, main use
      - address
      - applicants (requestor/owner/author)
      - parcels (gush/helka)
      - events history
    
    Includes CAPTCHA detection and retry logic.
    
    Args:
        permit_id: The permit number to fetch
        max_retries: Maximum number of retry attempts for CAPTCHA (default: 2)
        
    Returns:
        (mahut_text, metadata_dict)
    """
    url = API_URL_TEMPLATE.format(permit_id=permit_id)
    
    for attempt in range(max_retries + 1):
        try:
            response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            
            # Ensure proper encoding for Hebrew text
            response.encoding = response.apparent_encoding or 'utf-8'
            
            # Parse HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the div#mahut element containing "מהות הבקשה"
            mahut_div = soup.find('div', id='mahut')
            
            if mahut_div:
                # Get the text content, cleaned up
                text = mahut_div.get_text(separator=' ', strip=True)
                # Remove the header "מהות הבקשה" from the beginning if present
                text = text.replace('מהות הבקשה', '', 1).strip()
                # Clean up invisible Unicode control characters (RLM, LRM, etc.)
                text = text.replace('\u200f', '').replace('\u200e', '').strip()
                mahut_text = text if text else None
            else:
                # CAPTCHA detected - div#mahut not found
                if attempt < max_retries:
                    logger.warning(f"Permit {permit_id}: CAPTCHA detected (div#mahut not found), waiting 40s before retry {attempt + 1}/{max_retries}...")
                    print(f"\n🤖 CAPTCHA detected! Waiting 40 seconds before retry ({attempt + 1}/{max_retries})...")
                    time.sleep(40)
                    continue
                else:
                    logger.error(f"Permit {permit_id}: div#mahut not found after {max_retries + 1} attempts (likely CAPTCHA)")
                    return None, {}

            # Parse additional metadata
            request_info = _parse_request_info(soup)
            address = _parse_address(soup)
            applicants = _parse_applicants(soup)
            parcels = _parse_parcels(soup)
            history = _parse_history(soup)

            metadata = {
                "request_type": request_info.get("request_type"),
                "main_use": request_info.get("main_use"),
                "address": address,
                "applicants": applicants,
                "parcels": parcels,
                "history": history,
            }

            return mahut_text, metadata
                
        except requests.exceptions.Timeout:
            logger.error(f"Permit {permit_id}: Request timeout after {REQUEST_TIMEOUT}s")
            return None, {}
        except requests.exceptions.RequestException as e:
            logger.error(f"Permit {permit_id}: Request failed - {e}")
            return None, {}
        except Exception as e:
            logger.error(f"Permit {permit_id}: Unexpected error - {e}")
            return None, {}
    
    return None, {}  # Shouldn't reach here, but just in case


def log_model_request(permit_id: str, user_content: str):
    """
    Log the request being sent to the model for debugging.
    
    Args:
        permit_id: The permit ID
        user_content: The user message content being sent
    """
    # Use absolute path to ensure file is written to the correct location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(script_dir, DEBUG_REQUESTS_FILE)
    
    # Clean up invisible Unicode control characters (RLM, LRM, etc.)
    cleaned_content = user_content.replace('\u200f', '').replace('\u200e', '')
    
    try:
        with open(log_file_path, 'a', encoding='utf-8-sig') as f:
            f.write("=" * 80 + "\n")
            f.write(f"ID: {permit_id}\n")
            f.write(f"Request:\n{cleaned_content}\n")
            f.write("=" * 80 + "\n\n")
            f.flush()  # Force write to disk immediately
            os.fsync(f.fileno())  # Force OS to write to disk
    except Exception as e:
        logger.error(f"Failed to write to debug file: {e}")
        print(f"ERROR: Could not write to {log_file_path}: {e}")


def analyze_with_ai(mahut_text: str, permit_id: str, client: OpenAI, max_retries: int = 3) -> dict | None:
    """
    Send "מהות הבקשה" text to GPT-5-mini for investor opportunity analysis.
    Includes retry logic with exponential backoff for transient failures.
    
    Args:
        mahut_text: The extracted request intention text
        permit_id: The permit ID for reference
        client: OpenAI client instance
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Parsed JSON response from LLM, or None if analysis fails after all retries
    """
    for attempt in range(max_retries):
        try:
            user_content = f"Permit ID: {permit_id}\n\nמהות הבקשה:\n{mahut_text}"
            
            # Log the request being sent to the model (only on first attempt)
            if attempt == 0:
                log_model_request(permit_id, user_content)
            
            response = client.chat.completions.create(
                model="gpt-5-mini",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_content}
                ],
                response_format={"type": "json_object"}
            )
            
            # Extract the response text
            response_text = (response.choices[0].message.content or "").strip()
            if not response_text:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"Permit {permit_id}: Empty response (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Permit {permit_id}: AI returned empty response after {max_retries} attempts")
                    return None
            
            # Clean up potential markdown code blocks
            if response_text.startswith('```'):
                # Remove ```json and ``` markers
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1] if lines[-1] == '```' else lines[1:])
            
            # Parse JSON
            result = json.loads(response_text)
            
            # Ensure permit_id is in the result
            result['permit_id'] = permit_id
            
            return result
            
        except json.JSONDecodeError as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Permit {permit_id}: JSON parse error (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Permit {permit_id}: Failed to parse AI response as JSON after {max_retries} attempts - {e}")
                logger.debug(f"Raw response: {response_text if 'response_text' in locals() else 'N/A'}")
                return None
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Permit {permit_id}: AI call failed (attempt {attempt + 1}/{max_retries}), retrying in {wait_time}s... Error: {e}")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Permit {permit_id}: AI analysis failed after {max_retries} attempts - {e}")
                return None
    
    return None  # Shouldn't reach here, but just in case


def load_processed_permits(processed_file: str = "processed_permits.txt") -> set:
    """
    Load already-processed permit IDs to enable resume (includes both relevant and non-relevant).
    
    Args:
        processed_file: Path to file containing all processed permit IDs
        
    Returns:
        Set of permit IDs that have already been processed
    """
    if not os.path.exists(processed_file):
        return set()
    
    processed = set()
    try:
        with open(processed_file, 'r', encoding='utf-8') as f:
            for line in f:
                permit_id = line.strip()
                if permit_id:
                    processed.add(permit_id)
        logger.info(f"Loaded {len(processed)} already-processed permits from {processed_file}")
    except Exception as e:
        logger.warning(f"Could not load processed permits: {e}")
    
    return processed


def mark_permit_processed(permit_id: str, processed_file: str = "processed_permits.txt"):
    """
    Mark a permit as processed (regardless of relevance) to enable resume.
    
    Args:
        permit_id: The permit ID to mark as processed
        processed_file: Path to file tracking all processed permits
    """
    try:
        with open(processed_file, 'a', encoding='utf-8') as f:
            f.write(f"{permit_id}\n")
    except Exception as e:
        logger.error(f"Failed to mark {permit_id} as processed: {e}")


def save_opportunity_incremental(opportunity: Dict[str, Any], output_file: str = "opportunities.json", relevant_file: str = "relevant_permits.txt"):
    """
    Save a single relevant opportunity to JSON file immediately (incremental save).
    Also append the permit ID to relevant_permits.txt for resume capability.
    
    Args:
        opportunity: Dictionary containing permit data
        output_file: Path to JSON file
        relevant_file: Path to file tracking processed relevant permits
    """
    permit_id = opportunity.get('permit_id', 'unknown')
    
    # Load existing opportunities
    opportunities = []
    if os.path.exists(output_file):
        try:
            with open(output_file, 'r', encoding='utf-8') as f:
                opportunities = json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(f"Could not load existing {output_file}, starting fresh")
            opportunities = []
    
    # Append new opportunity
    opportunities.append(opportunity)
    
    # Save back to JSON
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(opportunities, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved permit {permit_id} to {output_file}")
    except Exception as e:
        logger.error(f"Failed to save opportunity {permit_id}: {e}")
    
    # Append to relevant_permits.txt for resume capability
    try:
        with open(relevant_file, 'a', encoding='utf-8') as f:
            f.write(f"{permit_id}\n")
    except Exception as e:
        logger.error(f"Failed to append {permit_id} to {relevant_file}: {e}")


def main():
    """
    Main workflow: read permits, fetch data, analyze with AI, save results.
    """
    print("=" * 60)
    print("Bat Yam Building Permit Analyzer - Stage 2 & 3")
    print("=" * 60)
    
    # Check for API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'your_api_key_here' or api_key == 'sk-your-api-key-here':
        print("\nERROR: OPENAI_API_KEY not configured!")
        print("   Please create a .env file with:")
        print("   OPENAI_API_KEY=sk-your-actual-api-key")
        return
    
    # Initialize OpenAI client
    client = OpenAI(api_key=api_key)
    print("OK: OpenAI client initialized")
    
    # Initialize debug requests file (clear previous content)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    log_file_path = os.path.join(script_dir, DEBUG_REQUESTS_FILE)
    try:
        with open(log_file_path, 'w', encoding='utf-8-sig') as f:
            f.write("Model Requests Debug Log\n")
            f.write("=" * 80 + "\n\n")
        print(f"OK: Debug log initialized: {log_file_path}")
    except Exception as e:
        logger.warning(f"Failed to initialize debug file: {e}")
    
    # Read permit IDs from file
    try:
        with open(PERMIT_FILE, 'r', encoding='utf-8') as f:
            permit_ids = [line.strip() for line in f if line.strip()]
        print(f"OK: Loaded {len(permit_ids)} permit IDs from {PERMIT_FILE}")
    except FileNotFoundError:
        print(f"\nERROR: {PERMIT_FILE} not found!")
        print("   Run the scraper first: python get_bakasha_numbers.py")
        return
    
    # Load already-processed permits for resume capability
    already_processed = load_processed_permits("processed_permits.txt")
    if already_processed:
        print(f"OK: Resume mode - {len(already_processed)} permits already processed")
        permit_ids_to_process = [pid for pid in permit_ids if pid not in already_processed]
        skipped_count = len(permit_ids) - len(permit_ids_to_process)
        print(f"OK: Skipping {skipped_count} already-processed permits")
        permit_ids = permit_ids_to_process
    
    if not permit_ids:
        print("\n" + "=" * 60)
        print("All permits already processed! Nothing to do.")
        print("=" * 60)
        return
    
    # Initialize results
    errors = []
    processed = 0
    relevant_count = 0
    requests_in_batch = 0  # Counter for batch cooldown
    
    print(f"\nProcessing {len(permit_ids)} permits...")
    print("-" * 60)
    
    # Process each permit
    for i, permit_id in enumerate(permit_ids, 1):
        print(f"[{i}/{len(permit_ids)}] Processing permit {permit_id}...", end=" ")
        
        # Fetch data from API
        mahut_text, metadata = fetch_permit_data(permit_id)
        
        if not mahut_text:
            print("ERROR: Failed to fetch")
            errors.append({
                'permit_id': permit_id,
                'error': 'Failed to fetch or extract מהות הבקשה'
            })
            mark_permit_processed(permit_id)  # Mark as processed even if failed
            # Smart throttle: random delay
            delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
            time.sleep(delay)
            requests_in_batch += 1
            continue
        
        # Analyze with AI
        result = analyze_with_ai(mahut_text, permit_id, client)
        
        if result is None:
            print("ERROR: AI analysis failed")
            errors.append({
                'permit_id': permit_id,
                'error': 'AI analysis failed'
            })
            mark_permit_processed(permit_id)  # Mark as processed even if failed
        elif result.get('is_relevant', False):
            project_type = result.get('project_type', 'Unknown')
            try:
                print(f"OK: RELEVANT - {project_type}")
            except UnicodeEncodeError:
                print(f"OK: RELEVANT (permit {permit_id})")
            # Attach parsed metadata
            enriched = {**result, **metadata}
            
            # Save immediately (incremental save)
            save_opportunity_incremental(enriched, OUTPUT_FILE, "relevant_permits.txt")
            relevant_count += 1
            mark_permit_processed(permit_id)  # Mark as processed
        else:
            reason = result.get('reason', 'Not relevant')
            # Encode reason safely for console (Windows console can't handle Hebrew)
            try:
                print(f"SKIP: Not relevant - {reason[:40]}...")
            except UnicodeEncodeError:
                print(f"SKIP: Not relevant (permit {permit_id})")
            mark_permit_processed(permit_id)  # Mark as processed
        
        processed += 1
        requests_in_batch += 1
        
        # Smart throttle: random delay between requests
        delay = random.uniform(REQUEST_DELAY_MIN, REQUEST_DELAY_MAX)
        time.sleep(delay)
        
        # Batch cooldown: every 10 requests, take a longer break
        if requests_in_batch >= BATCH_SIZE and i < len(permit_ids):
            print(f"\n⏸️  Batch cooldown: Processed {BATCH_SIZE} requests, pausing for {BATCH_COOLDOWN}s to avoid blocking...")
            time.sleep(BATCH_COOLDOWN)
            requests_in_batch = 0  # Reset counter
            print("✅ Cooldown complete, resuming...\n")
    
    # Save results
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)
    
    # Opportunities were saved incrementally during processing
    print(f"OK: All relevant permits saved incrementally to {OUTPUT_FILE}")
    print(f"OK: Relevant permit IDs tracked in relevant_permits.txt")
    
    # Summary
    print(f"\nSummary:")
    print(f"  - Total permits processed: {processed}")
    print(f"  - Investor opportunities found: {relevant_count}")
    print(f"  - Errors: {len(errors)}")
    
    # Show opportunities from file
    if relevant_count > 0:
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                saved_opportunities = json.load(f)
            print(f"\nTop Opportunities:")
            for opp in saved_opportunities[-5:]:  # Show last 5 from this run
                try:
                    print(f"  - {opp['permit_id']}: {opp.get('project_type', 'N/A')}")
                    if opp.get('num_units'):
                        print(f"    Units: {opp['num_units']}")
                except UnicodeEncodeError:
                    print(f"  - {opp['permit_id']} (see opportunities.json for details)")
        except Exception as e:
            logger.warning(f"Could not read opportunities for summary: {e}")


if __name__ == "__main__":
    main()

