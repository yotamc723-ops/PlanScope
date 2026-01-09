from bs4 import BeautifulSoup
import sys

def _get_text(el) -> str:
    if not el: return None
    txt = el.get_text(separator=" ", strip=True)
    return txt.replace('\u200f', '').replace('\u200e', '').strip()

def visualize_table(html_path):
    with open(html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'html.parser')
    rows = soup.find_all('tr')
    
    current_phaze = "NO PHASE"
    
    print(f"{'TYPE':<10} | {'CONTENT':<50} | {'STATUS'}")
    print("-" * 80)

    for i, row in enumerate(rows):
        cells = row.find_all(['td', 'th'])
        if not cells: continue
        
        # Logic to test
        is_header = False
        row_class = row.get('class', [])
        
        # Check 1: Accordion class
        if row_class and any('accordion' in c for c in row_class):
            is_header = True
        # Check 2: Single cell spanning
        elif len(cells) == 1 and cells[0].has_attr('colspan'):
            is_header = True
        # Check 3: Strong tag in single cell
        elif len(cells) == 1 and cells[0].find('strong'):
            is_header = True

        if is_header:
            raw_text = _get_text(cells[0])
            # Cleaning logic
            clean_text = raw_text
            if '(' in clean_text and clean_text.endswith(')'):
                 try: 
                     clean_text = clean_text.rsplit('(', 1)[0].strip()
                 except: pass
            
            current_phaze = clean_text
            print(f"HEADER     | {current_phaze:<50} | ---")
            continue

        # Data Row
        if len(cells) >= 3:
            req_desc = _get_text(cells[0])
            req_status = _get_text(cells[1])
            
            # Formatting
            if req_desc.startswith("-"): req_desc = req_desc.lstrip("-").strip()
            
            print(f"DATA       |   -> {req_desc[:45]:<45} | {req_status}")

if __name__ == "__main__":
    visualize_table('/Users/yotamcohen/Desktop/PlanScope/PlanScope_Scrapers/permits/requirments_table.txt')
