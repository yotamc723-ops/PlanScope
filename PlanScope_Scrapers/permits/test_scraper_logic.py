from bs4 import BeautifulSoup
import logging

# Setup basic logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def _get_text(el) -> str:
    """Return stripped text from a BeautifulSoup element."""
    if not el:
        return None
    txt = el.get_text(separator=" ", strip=True)
    txt = txt.replace('\u200f', '').replace('\u200e', '').strip()
    return txt if txt else None

def parse_requirements_level(soup: BeautifulSoup):
    """
    Parses the 'Requirements Level' from the specific requirements table.
    """
    try:
        # The ID in the HTML is misspelled as 'table-requirments'
        table = soup.find('table', id='table-requirments')
        if not table:
            # Fallback checking for corrected spelling just in case
            table = soup.find('table', id='table-requirements')
        
        if not table:
            print("Table not found")
            return None

        stages = []
        current_category = "General" # Default if no header found first
        
        # Iterate over all rows in the table body
        tbody = table.find('tbody')
        rows = tbody.find_all('tr') if tbody else table.find_all('tr')
        
        for i, row in enumerate(rows):
            cells = row.find_all(['td', 'th'])
            if not cells:
                continue
            
            # --- IDENTIFY HEADER ---
            # User says headers have strong text and colspan=4, or class="accordion-toggle"
            is_header = False
            
            # Check 1: Accordion class
            if row.get('class') and 'accordion-toggle' in row.get('class'):
                is_header = True
            
            # Check 2: Single cell spanning (colspan=4) with strong
            elif len(cells) == 1 and cells[0].has_attr('colspan'):
                is_header = True
                
            # Check 3: Just strong text in a single cell row (fallback)
            elif len(cells) == 1 and cells[0].find('strong'):
                is_header = True

            if is_header:
                # Extract text, removing any (count) numbers if present
                # Example: "תנאים לקליטת בקשה להיתר ( 12)"
                full_text = _get_text(cells[0])
                # Check for strong specifically if possible to be cleaner
                strong_tag = cells[0].find('strong')
                if strong_tag:
                    # Sometimes there are multiple strongs, e.g. Name + Count
                    # We usually want the first one or the concatenated text
                    # The user example: <strong class="spn">Title</strong> <strong class="spn">(4)</strong>
                    current_category = full_text
                    
                    # Clean up the "( 12)" part if we want just the title
                    if '(' in current_category and ')' in current_category and current_category.endswith(')'):
                        # Simple heuristic: remove trailing parenthetical count
                        current_category = current_category.rsplit('(', 1)[0].strip()
                else:
                    current_category = full_text

                print(f"DEBUG: Found Category: {current_category}")
                continue

            # --- IDENTIFY DATA ---
            # Data rows usually have 3+ cells: Req | Status | Date | ...
            if len(cells) >= 3:
                req_desc = _get_text(cells[0])
                req_status = _get_text(cells[1])
                req_date = _get_text(cells[2])
                
                # Cleanup description
                if req_desc and req_desc.startswith("-"):
                    req_desc = req_desc.lstrip("-").strip()
                
                if req_desc:
                    print(f"  -> Found Req: {req_desc} | {req_status}")
                    stages.append({
                        "category": current_category,
                        "requirement": req_desc,
                        "status": req_status,
                        "date": req_date
                    })

        return stages

    except Exception as e:
        print(f"Error parsing requirements level: {e}")
    
    return None

# User provided HTML Snippet
html_content = """
<div id="table-requirments">
<table class="table table-condensed" id="table-requirments">
      <thead>
        <tr>
          <th class="th-results-header" translatable-text="">דרישה</th>
          <th class="th-results-header" translatable-text="">סטטוס</th>
          <th class="th-results-header" translatable-text="">תאריך</th>
          <th class="th-results-header hidden-on-mobile" translatable-text="">
            הערות
          </th>
        </tr>
      </thead>
      <tbody>
                                <tr>
          <td colspan="4">
            <strong>איכות הסביבה - בקשה למידע</strong>
          </td>
        </tr>
                        <tr class="">
          <td>התייחסות לבקשה למידע - איכות הסביבה</td>
          <td class="no-wrap">הושלם</td>
          <td>10/03/2025</td>
          <td class="hidden-on-mobile">
                      </td>
        </tr>
        
                        <tr class="accordion-toggle collapsed" onclick="toggelDrishot(this,'rqs1')">
          <td colspan="4">
            <strong class="spn">תנאים לקליטת בקשה להיתר</strong>
            <strong class="spn">( 12)</strong>
          </td>
        </tr>
                
        <tr class="rqs1 tr-hidden">
          <td>תוספות:</td>
          <td class="no-wrap">לא הושלם</td>
          <td></td>
          <td class="hidden-on-mobile">
                      </td>
        </tr>
        <tr class="rqs1 tr-hidden">
          <td>- תיק מידע בתוקף</td>
          <td class="no-wrap">לא הושלם</td>
          <td></td>
          <td class="hidden-on-mobile">
                      </td>
        </tr>
      </tbody>
</table>
</div>
"""

def main():
    soup = BeautifulSoup(html_content, 'html.parser')
    results = parse_requirements_level(soup)
    print("\n--- Final Results ---")
    for r in results:
        print(r)

if __name__ == "__main__":
    main()
