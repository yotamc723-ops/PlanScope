# Repository Map: PlanScope

```text
PlanScope/
├── PlanScope_UI/ (Frontend dashboard)
│   ├── app/
│   ├── components/
│   ├── config/
│   ├── docs/
│   ├── functions/ (Firebase Cloud Functions)
│   ├── services/
│   ├── utils/
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── PlanScope_Scrapers/ (Data collection scripts)
│   ├── daily_reports/ (Unified reports)
│   ├── permits/ (Permit scraping logic)
│   │   ├── diff/
│   │   ├── permit_numbers/
│   │   ├── permits_data/
│   │   ├── analyze_permits.py
│   │   ├── daily_permit_scraper.py
│   │   └── main_permit.py
│   ├── taba/ (Taba/Planning scraping)
│   │   ├── diff/
│   │   ├── plans_data/
│   │   ├── get_information_taba.py
│   │   └── main_taba.py
│   ├── yeshivot/ (Meeting protocols scraping)
│   │   ├── decision_protocols/
│   │   ├── processed_json/
│   │   ├── processed_texts/
│   │   ├── daily_yeshivot_scanner.py
│   │   └── yeshivot_scraper.py
│   └── main_scraper.py
├── firebase/ (Firebase configuration files)
│   ├── firestore.rules
│   ├── firestore.indexes.json
│   └── firebase.json
├── .env.example
├── .gitignore
├── bat_yam_taba_list.csv
└── REPO_MAP.md (This file)
```
