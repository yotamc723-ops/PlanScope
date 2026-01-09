import requests
from bs4 import BeautifulSoup

url = "https://handasi.complot.co.il/magicscripts/mgrqispi.dll?appname=cixpa&prgname=GetBakashaFile&siteid=81&b=20250079&arguments=siteid,b"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
}

try:
    print(f"Fetching {url}...")
    r = requests.get(url, headers=headers, timeout=30, verify=False)
    soup = BeautifulSoup(r.text, 'html.parser')
    
    table = soup.find('table', id='table-requirments')
    print(f"Find by ID 'table-requirments': {table is not None}")
    
    table2 = soup.find('table', id='table-requirements')
    print(f"Find by ID 'table-requirements': {table2 is not None}")
    
    if not table and not table2:
        print("Searching for table by content...")
        found = False
        # Look for table with header "דרישה"
        for t in soup.find_all('table'):
            if "דרישה" in t.text and "סטטוס" in t.text:
                print("Found table by content matches!")
                print(f"Table classes: {t.get('class')}")
                print(f"Table ID: {t.get('id')}")
                found = True
                break
        
        if not found:
            print("Table NOT found in content either.")
    
    with open('debug_fetch.html', 'w', encoding='utf-8') as f:
        f.write(r.text)
    print("Saved HTML to debug_fetch.html")

except Exception as e:
    print(f"Error: {e}")
