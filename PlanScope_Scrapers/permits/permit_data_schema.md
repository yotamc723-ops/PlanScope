# City Plan (Taba) Data Structure Schema

This document defines the data structure for **City Plans (Taba)** extracted by the Bat Yam Taba scraper.
Note: This schema corresponds to files like `bat_yam_plans_data_YYYY_MM_DD.json`.

---

## 📊 Data Schema

Each plan is represented as a JSON object with the following fields:

### Root Level Fields

| Field Name | Type | Description | Source |
|------------|------|-------------|--------|
| `plan_number` | string | Unique plan identifier (e.g., "502-0126813") | API/HTML |
| `plan_type` | string | Type of plan (e.g., "תכנית מתאר מקומית") | API/HTML |
| `plan_name` | string | Name/Title of the plan (e.g., "בי/534 מבנים בעירוב שימושים") | API/HTML |

---

### Nested Objects

#### `general_info` (object)
Detailed administrative information about the plan:

| Field Name | Type | Description |
|------------|------|-------------|
| `status` | string | Current status (e.g., "בתוקף", "בתכנון") |
| `status_date` | string | Date of the status change (DD/MM/YYYY) |
| `authority` | string | Responsible authority (e.g., "ועדה מחוזית", "ועדה מקומית") |
| `neighborhood` | string/null | Neighborhood name (often "nan" if unavailable) |
| `area` | string | Area textual description (e.g., "16,797.00 מ\"ר 16.797 דונם") |
| `developer` | string/null | Developer name (e.g., "ארז דהבני") |
| `mavat_link` | string | Direct URL to the Mavat system for this plan |

---

#### `history` (array of arrays)
Chronological list of plan events. Each item is a list (tuple) of exactly two strings:

Format: `[ "Date", "Description" ]`

| Index | Type | Description |
|-------|------|-------------|
| 0 | string | Event date (DD/MM/YYYY) |
| 1 | string | Event description (e.g., "ש800 בתוקף - מסגירת תיק תכנון") |

**Example:**
```json
[
  ["09/01/2018", "ש800 בתוקף - מסגירת תיק תכנון"],
  ["04/06/2025", "התכנית/היישות נדונה בוועדה מקומית"]
]
```

---

#### `meeting_history` (array of objects)
List of committee meetings related to the plan:

| Field Name | Type | Description |
|------------|------|-------------|
| `meeting_type` | string | Type of meeting (e.g., "ועדת משנה", "ועדת שימור אתרים") |
| `meeting_number` | string | Unique meeting ID (e.g., "20140002") |
| `meeting_date` | string | Date of the meeting (DD/MM/YYYY) |
| `day_of_week` | string | Hebrew day abbreviation (e.g., "א", "ב") |
| `meeting_time` | string | Time of meeting (HH:MM) |
| `meeting_link` | string | Direct URL to the meeting protocols |

---

## 📋 Example: Complete Plan Record

```json
{
    "plan_number": "502-0126813",
    "plan_type": "תכנית מתאר מקומית",
    "plan_name": "בי/534 מבנים בעירוב שימושים",
    "general_info": {
        "status": "בתוקף",
        "status_date": "09/01/2018",
        "authority": "ועדה מחוזית",
        "neighborhood": "nan",
        "area": "16,797.00 מ\"ר 16.797 דונם",
        "developer": "ארז דהבני",
        "mavat_link": "https://mavat.iplan.gov.il/SV3?text=502-0126813"
    },
    "history": [
        ["09/01/2018", "ש800 בתוקף - מסגירת תיק תכנון"],
        ["04/06/2025", "התכנית/היישות נדונה בוועדה מקומית"]
    ],
    "meeting_history": [
        {
            "meeting_type": "ועדת משנה",
            "meeting_number": "20140002",
            "meeting_date": "27/04/2014",
            "day_of_week": "א",
            "meeting_time": "00:00",
            "meeting_link": "https://batyam.complot.co.il/binyan/#meeting/2/20140002"
        }
    ]
}
```

---

## 📝 Notes

1.  **Date Format**: All dates are strictly `DD/MM/YYYY`.
2.  **Null Values**: Some fields like `neighborhood` or `developer` may contain the string `"nan"` or be null if scraped from empty cells.
3.  **History Structure**: Unlike permits, the history here is a simple list of lists, not a list of objects with named keys.
