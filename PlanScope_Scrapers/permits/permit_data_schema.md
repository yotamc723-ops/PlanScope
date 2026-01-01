# Building Permit Data Structure Schema

This document defines the complete data structure for a single building permit request as extracted by the Bat Yam permit analyzer.

---

## 📊 Data Schema

Each permit request is represented as a JSON object with the following fields:

### Root Level Fields

| Field Name | Type | Description | Source |
|------------|------|-------------|--------|
| `is_relevant` | boolean | Whether the permit is relevant for real estate investors | AI Analysis |
| `permit_id` | string | Unique permit identification number (8 digits) | API |
| `project_type` | string | Classification of the project (e.g., "הריסה ובנייה", "Tama 38") | AI Analysis |
| `description` | string | Full Hebrew description of the permit request (מהות הבקשה) | API (div#mahut) |
| `num_units` | number/null | Number of residential units in the project | AI Analysis |
| `key_features` | array[string] | AI-extracted key features and investment insights | AI Analysis |
| `request_type` | string | Type of permit request (e.g., "בקשה למידע", "בקשה להיתר") | API (info table) |
| `main_use` | string | Primary use classification (e.g., "מגורים", "מסחר") | API (info table) |
| `address` | string | Full street address of the property | API (navbar) |

### Nested Objects

#### `applicants` (object)
Information about parties involved in the permit request:

| Field Name | Type | Description |
|------------|------|-------------|
| `requestor` | string/null | Name of the party submitting the request (מבקש) |
| `owner` | string/null | Name of the property owner (בעל הנכס) |
| `author` | string/null | Name of the architect/planner (עורך) |

#### `parcels` (array of objects)
Land parcel identification (גוש וחלקה):

| Field Name | Type | Description |
|------------|------|-------------|
| `gush` | string | Gush number (גוש) - land block identifier |
| `helka` | string | Helka number (חלקה) - parcel identifier |

#### `history` (array of objects)
Chronological permit processing events (אירועים):

| Field Name | Type | Description |
|------------|------|-------------|
| `event_type` | string | Event status (e.g., "נוכחי", "סגור") |
| `event_description` | string | Description of the event |
| `event_date` | string | Event start date (DD/MM/YYYY) |
| `event_end_date` | string/null | Event end date (DD/MM/YYYY) or null if ongoing |

---

## 📋 Example: Complete Permit Record

```json
{
  "is_relevant": true,
  "permit_id": "20250954",
  "project_type": "הריסה ובנייה",
  "description": "מידע עבור תכנית במסלול רישוי מהיר לפי תיקון 139 שמהותה הריסת 2 מבנים בעלי קיר משותף כל אחד בן 4 קומות, הכוללים סה\"כ 32 יח\"ד, והקמת מבנה מגורים בן 10 קומות, הכולל סה\"כ 80 יח\"ד",
  "num_units": 80,
  "key_features": [
    "הריסה של 2 מבנים קיימים בעלי קיר משותף",
    "מבנים קיימים: כל אחד 4 קומות, יחדיו 32 יח\"ד",
    "הקמה של מבנה מגורים חדש בן 10 קומות",
    "סך הכל 80 יחידות דיור במבנה החדש",
    "תכנית במסלול רישוי מהיר לפי תיקון 139"
  ],
  "request_type": "בקשה למידע",
  "main_use": "מגורים",
  "address": "מנדלי מוכר ספרים 11 בת ים",
  "applicants": {
    "requestor": "קבוצת אהרוני",
    "owner": "טל נבות",
    "author": null
  },
  "parcels": [
    {
      "gush": "7136",
      "helka": "360"
    },
    {
      "gush": "7136",
      "helka": "361"
    }
  ],
  "history": [
    {
      "event_type": "נוכחי",
      "event_description": "דחיית בקשה למידע - אי עמידה בתנאי סף",
      "event_date": "28/12/2025",
      "event_end_date": null
    },
    {
      "event_type": "סגור",
      "event_description": "קבלת נתונים מרישוי זמין",
      "event_date": "28/12/2025",
      "event_end_date": "28/12/2025"
    },
    {
      "event_type": "סגור",
      "event_description": "פתיחת בקשה למידע",
      "event_date": "28/12/2025",
      "event_end_date": "28/12/2025"
    }
  ]
}
```

---

## 🔍 Field Value Examples

### `is_relevant`
- `true` - Relevant for investors (demolition/construction, new developments, Tama 38, etc.)
- `false` - Not relevant (minor renovations, cosmetic changes, small add-ons)

### `project_type` (when relevant)
- `"הריסה ובנייה"` (Demolition and Construction)
- `"Pinui Binui / הריסה ובנייה"` (Urban Renewal)
- `"Tama 38"` (National Outline Plan 38)
- `"הריסה ובנייה (Demolition and Construction)"`

### `request_type`
- `"בקשה למידע"` (Information Request)
- `"בקשה להיתר - רישוי מלא"` (Full Permit Request)
- `"בקשה להיתר - רישוי מהיר"` (Fast-Track Permit Request)

### `main_use`
- `"מגורים"` (Residential)
- `"מסחר"` (Commercial)
- `"תעשייה"` (Industrial)
- `"מבני ציבור"` (Public Buildings)
- `"בניה חדשה - מגורים, תעסוקה, מסחר, מבני ציבור"` (Mixed Use)

### `event_type`
- `"נוכחי"` (Current/Active)
- `"סגור"` (Closed/Completed)

---

## 📝 Notes for LLM Processing

1. **Hebrew Text**: All fields containing Hebrew text use UTF-8 encoding without BOM. Right-to-left (RTL) control characters have been cleaned.

2. **Null Values**: Fields may be `null` when data is not available from the source. Common null fields: `author`, `num_units`, `event_end_date`.

3. **Arrays**: `key_features`, `parcels`, and `history` are always arrays, but may be empty `[]` if no data exists.

4. **Date Format**: All dates use DD/MM/YYYY format (e.g., "28/12/2025").

5. **Permit ID**: Always 8 digits, representing the year and sequence (e.g., 20250954 = year 2025, sequence 954).

6. **Gush/Helka**: Israeli land registry identifiers. Multiple parcels indicate the project spans multiple plots.

---

## 🎯 Data Source Summary

| Data Category | Source Location | Extraction Method |
|---------------|-----------------|-------------------|
| Basic Info | API HTML Response | BeautifulSoup CSS selectors |
| Description | `div#mahut` | BeautifulSoup |
| Administrative | `#info-main table` | Table row parsing |
| Address | `#navbar-titles-id` h5[3] | Navbar parsing |
| Applicants | `#table-baaley-inyan` | Table parsing |
| Parcels | `#table-gushim-helkot` | Table parsing |
| History | `#table-events` | Table row parsing |
| AI Analysis | OpenAI GPT-4o-mini | LLM analysis of description |

---

*Generated for: Bat Yam Building Permit Analyzer*  
*Last Updated: 2025-12-30*

