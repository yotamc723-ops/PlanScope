import { MeetingSummary, MeetingDetail, PermitSummary, PermitDetail, ApplicationPublication, PlanPublication } from '../types';

// --- DATA GENERATORS ---

const STREETS = ['בלפור', 'יוספטל', 'הרצל', 'רוטשילד', 'העצמאות', 'סוקולוב', 'ירושלים', 'הנביאים', 'אנה פרנק', 'הגבול', 'הקוממיות', 'בן גוריון', 'אילת', 'ניסנבוים'];
const APPLICANTS = ['אאורה ישראל', 'י.ח. דמרי', 'אזורים', 'פרשקובסקי', 'עיריית בת ים', 'קבוצת מבנה', 'אשדר', 'אפריקה ישראל', 'שיכון ובינוי', 'פרטי'];
const ARCHITECTS = ['משה צור', 'יסקי מור סיון', 'קיקה ברא"ז', 'טעמון אדריכלים', 'בר אוריין', 'פייגין אדריכלים', 'כנפו כלימור'];

const getRandom = (arr: any[]) => arr[Math.floor(Math.random() * arr.length)];
const getRandomInt = (min: number, max: number) => Math.floor(Math.random() * (max - min + 1)) + min;

// --- MEETINGS ---

export const DEMO_MEETINGS: MeetingSummary[] = [
  { id: 'dm-1', city: 'בת ים', meeting_id: '2023020', meeting_date: '2023-11-01T16:00:00Z', decisions_count: 15 },
  { id: 'dm-2', city: 'בת ים', meeting_id: '2023019', meeting_date: '2023-10-25T14:00:00Z', decisions_count: 8 },
  { id: 'dm-3', city: 'בת ים', meeting_id: '2023018', meeting_date: '2023-10-15T09:00:00Z', decisions_count: 22 },
  { id: 'dm-4', city: 'בת ים', meeting_id: '2023017', meeting_date: '2023-09-28T10:30:00Z', decisions_count: 12 },
  { id: 'dm-5', city: 'בת ים', meeting_id: '2023016', meeting_date: '2023-09-10T12:00:00Z', decisions_count: 5 },
  { id: 'dm-6', city: 'בת ים', meeting_id: '2023015', meeting_date: '2023-08-25T08:30:00Z', decisions_count: 18 },
  { id: 'dm-7', city: 'בת ים', meeting_id: '2023014', meeting_date: '2023-08-01T15:00:00Z', decisions_count: 9 },
  { id: 'dm-8', city: 'בת ים', meeting_id: '2023013', meeting_date: '2023-07-15T09:00:00Z', decisions_count: 30 },
];

// --- PERMITS ---

export const DEMO_PERMITS: PermitSummary[] = [
  {
    id: 'dp-1', city: 'בת ים', request_id: '2023-1550', permit_date: '2023-11-02T00:00:00Z',
    request_type: 'תמ"א 38/2', essence: 'הריסת בניין קיים בן 4 קומות והקמת בניין חדש בן 10 קומות.',
    gush: '7144', helka: '25'
  },
  {
    id: 'dp-2', city: 'בת ים', request_id: '2023-1420', permit_date: '2023-10-30T00:00:00Z',
    request_type: 'שינוי חזית', essence: 'סגירת מרפסות חורף בקומה א\' ו-ב\'.',
    gush: '7130', helka: '10'
  },
  {
    id: 'dp-3', city: 'בת ים', request_id: '2023-1300', permit_date: '2023-10-25T00:00:00Z',
    request_type: 'בנייה חדשה', essence: 'הקמת מגדל מגורים בן 40 קומות בפארק הים.',
    gush: '7155', helka: '2'
  },
  {
    id: 'dp-4', city: 'בת ים', request_id: '2023-1250', permit_date: '2023-10-15T00:00:00Z',
    request_type: 'שימוש חורג', essence: 'היתר לשימוש חורג לגן ילדים בקומת קרקע.',
    gush: '7122', helka: '50'
  },
  {
    id: 'dp-5', city: 'בת ים', request_id: '2023-1100', permit_date: '2023-10-05T00:00:00Z',
    request_type: 'תוספת בנייה', essence: 'תוספת ממ"דים לעורף המבנה הקיים.',
    gush: '7140', helka: '12'
  },
  {
    id: 'dp-6', city: 'בת ים', request_id: '2023-1050', permit_date: '2023-09-20T00:00:00Z',
    request_type: 'תמ"א 38/1', essence: 'חיזוק ועיבוי, תוספת 2.5 קומות ומעלית.',
    gush: '7135', helka: '8'
  },
  {
    id: 'dp-7', city: 'בת ים', request_id: '2023-0900', permit_date: '2023-09-10T00:00:00Z',
    request_type: 'שינויים פנימיים', essence: 'איחוד דירות ושינוי מחיצות פנימיות.',
    gush: '7120', helka: '33'
  },
   {
    id: 'dp-8', city: 'בת ים', request_id: '2023-0850', permit_date: '2023-09-01T00:00:00Z',
    request_type: 'לגליזציה', essence: 'הכשראת פרגולה ומחסן בחצר.',
    gush: '7125', helka: '4'
  }
];

// --- APPLICATIONS ---

export const DEMO_APPLICATIONS: ApplicationPublication[] = [
    {
        id: 'da-1', city: 'בת ים', request_id: '2024-0012', published_at: '2023-11-03T00:00:00Z',
        applicant_name: 'אאורה ישראל', description: 'בקשה להקלה בקווי בניין עבור פרויקט פינוי בינוי במתחם יוספטל.',
        gush: '7150', helka: '10-20'
    },
    {
        id: 'da-2', city: 'בת ים', request_id: '2024-0010', published_at: '2023-11-01T00:00:00Z',
        applicant_name: 'פרטי', description: 'בקשה לתוספת מרפסת שמש בחזית קדמית.',
        gush: '7122', helka: '5'
    },
    {
        id: 'da-3', city: 'בת ים', request_id: '2024-0005', published_at: '2023-10-28T00:00:00Z',
        applicant_name: 'עיריית בת ים', description: 'הקמת מבנה ציבור חדש (מתנ"ס) בשכונת רמת הנשיא.',
        gush: '7130', helka: '100'
    },
    {
        id: 'da-4', city: 'בת ים', request_id: '2023-9990', published_at: '2023-10-25T00:00:00Z',
        applicant_name: 'בסר הנדסה', description: 'שינוי הוראות בינוי במתחם העסקים, תוספת זכויות למסחר.',
        gush: '7160', helka: '1'
    },
    {
        id: 'da-5', city: 'בת ים', request_id: '2023-9980', published_at: '2023-10-20T00:00:00Z',
        applicant_name: 'אשדר', description: 'בקשה להיתר חפירה ודיפון.',
        gush: '7145', helka: '30'
    },
    {
        id: 'da-6', city: 'בת ים', request_id: '2023-9950', published_at: '2023-10-15T00:00:00Z',
        applicant_name: 'פרטי', description: 'הקמת בריכת שחייה בחצר בית פרטי.',
        gush: '7120', helka: '12'
    }
];

// --- PLANS ---

export const DEMO_PLANS: PlanPublication[] = [
    {
        id: 'dpl-1', city: 'בת ים', plan_number: '502-0998877', published_at: '2023-11-01T00:00:00Z',
        message_type: 'הודעה בדבר אישור תכנית', plan_goal: 'התחדשות עירונית - מתחם השבטים',
        plan_main_points: 'קביעת זכויות בנייה ל-6 מגדלי מגורים, שטחי מסחר ומבני ציבור. סה"כ 900 יח"ד.',
        gush: '7140', helka: 'All'
    },
    {
        id: 'dpl-2', city: 'בת ים', plan_number: '502-0887766', published_at: '2023-10-20T00:00:00Z',
        message_type: 'הודעה בדבר הפקדת תכנית', plan_goal: 'פארק הים - הרחבת טיילת',
        plan_main_points: 'שינוי ייעוד משצ"פ לדרך, הרחבת טיילת החוף וקביעת הוראות בינוי לקיוסקים.',
        gush: '7155', helka: '15'
    },
    {
        id: 'dpl-3', city: 'בת ים', plan_number: '502-0776655', published_at: '2023-10-10T00:00:00Z',
        message_type: 'הודעה בדבר מתן תוקף', plan_goal: 'מתחם התעסוקה החדש',
        plan_main_points: 'תוספת זכויות בנייה למשרדים, שינוי קווי בניין והגדלת תכסית.',
        gush: '7160', helka: 'Various'
    },
    {
        id: 'dpl-4', city: 'בת ים', plan_number: '502-0665544', published_at: '2023-09-25T00:00:00Z',
        message_type: 'הודעה על הכנת תכנית', plan_goal: 'שימור מבנים במרכז העיר',
        plan_main_points: 'הכנת רשימת שימור למבני באוהאוס ברחובות רוטשילד וירושלים.',
        gush: '7125', helka: 'Multiple'
    },
    {
        id: 'dpl-5', city: 'בת ים', plan_number: '502-0554433', published_at: '2023-09-01T00:00:00Z',
        message_type: 'הודעה בדבר דחיית תכנית', plan_goal: 'תחנת דלק רחוב הקוממיות',
        plan_main_points: 'הוועדה המחוזית החליטה לדחות את התכנית להקמת תחנת דלק עקב קרבה למבני מגורים.',
        gush: '7130', helka: '50'
    }
];

// --- DETAILS GENERATORS ---

export const DEMO_MEETING_DETAILS: Record<string, MeetingDetail> = {};
DEMO_MEETINGS.forEach(m => {
    const items = [];
    const count = m.decisions_count;
    for(let i=0; i<count; i++) {
        const street = getRandom(STREETS);
        const houseNum = getRandomInt(1, 150);
        const type = getRandom(['תמ"א 38', 'פינוי בינוי', 'שימוש חורג', 'הקלה', 'בנייה חדשה']);
        const status = getRandom(['אושר בתנאים', 'נדחה', 'לדיון נוסף', 'הפקדה', 'אושר להיתר']);
        
        items.push({
            id: `mi-${m.id}-${i}`,
            request_id: `2023-${getRandomInt(1000, 9999)}`,
            decision: status,
            status: status === 'אושר בתנאים' ? 'הוועדה מאשרת את הבקשה בכפוף לתנאים' : 'הבקשה נדחית',
            subject: `רחוב ${street} ${houseNum}, בת ים`,
            description: `בקשה ל${type}: הקמת בניין מגורים, תוספת זכויות והקלות בקווי בניין.`,
            applicant: getRandom(APPLICANTS),
            units: getRandomInt(10, 100),
            valid_until: '2025-12-31'
        });
    }

    DEMO_MEETING_DETAILS[m.id] = {
        ...m,
        document_url: '#',
        created_at: new Date().toISOString(),
        meeting_items: items
    };
});

export const DEMO_PERMIT_DETAILS: Record<string, PermitDetail> = {};
DEMO_PERMITS.forEach(p => {
    DEMO_PERMIT_DETAILS[p.id] = {
        ...p,
        created_at: p.permit_date || new Date().toISOString(),
        applicant_name: getRandom(APPLICANTS),
        architect: getRandom(ARCHITECTS),
        total_area: `${getRandomInt(500, 10000)} מ"ר`,
        license_id: `LIC-${getRandomInt(10000, 99999)}`
    };
});

// Since types match exactly, we can just use the arrays for lookups if we don't need extra detail fields not present in summary.
// But for consistency let's pretend we fetch full details.
export const DEMO_APPLICATION_DETAILS: Record<string, ApplicationPublication> = {};
DEMO_APPLICATIONS.forEach(a => {
    DEMO_APPLICATION_DETAILS[a.id] = {
        ...a,
        status: 'בבדיקה',
        last_update: '2023-11-04T09:00:00Z',
        filing_date: '2023-09-01'
    };
});

export const DEMO_PLAN_DETAILS: Record<string, PlanPublication> = {};
DEMO_PLANS.forEach(p => {
    DEMO_PLAN_DETAILS[p.id] = {
        ...p,
        depositing_date: '2023-10-01',
        status: 'בתוקף',
        area_dunam: getRandomInt(5, 50)
    };
});