import { MeetingSummary, MeetingDetail, PermitSummary, PermitDetail, ApplicationPublication, PlanPublication } from '../types';

export const MOCK_MEETINGS: MeetingSummary[] = [
  {
    id: 'a1b2c3d4-e5f6-7890-1234-567890abcdef',
    city: 'תל אביב - יפו',
    meeting_id: '2023044',
    meeting_date: '2023-10-15T09:00:00Z',
    decisions_count: 42
  },
  {
    id: 'f1e2d3c4-b5a6-0987-6543-210987fedcba',
    city: 'ירושלים',
    meeting_id: '2023042',
    meeting_date: '2023-10-12T14:30:00Z',
    decisions_count: 15
  },
  {
    id: '98765432-1234-5678-90ab-cdef12345678',
    city: 'חיפה',
    meeting_id: '2023039',
    meeting_date: '2023-10-10T11:00:00Z',
    decisions_count: 8
  }
];

export const MOCK_PERMITS: PermitSummary[] = [
  {
    id: '12345678-90ab-cdef-1234-567890abcdef',
    city: 'ראשון לציון',
    request_id: '2023-0552',
    permit_date: '2023-10-18T00:00:00Z',
    request_type: 'בנייה חדשה',
    essence: 'תכנית פינוי-בינוי: הריסת 3 מבנים והקמת מבנה עירוב שימושים (קומת קרקע מסחרית ושב"צ + 8.5 קומות מגורים) ומגדל עירוב שימושים הכולל קומה ציבורית ומגדל מגורים בן 25 קומות; הקצאת שטחי ציבור והגדלת זכויות למגורים.',
    gush: '3945',
    helka: '12'
  },
  {
    id: 'abcdef12-3456-7890-abcd-ef1234567890',
    city: 'פתח תקווה',
    request_id: '2023-1102',
    permit_date: '2023-10-16T00:00:00Z',
    request_type: 'תוספת בנייה',
    essence: 'תוספת ממ"ד ומרפסת שמש לדירה קיימת בקומה 3',
    gush: '6355',
    helka: '44'
  },
  {
    id: 'aaaa1111-bb22-cc33-dd44-ee5566778899',
    city: 'באר שבע',
    request_id: '2023-0099',
    permit_date: null,
    request_type: 'שינויים פנימיים',
    essence: 'שינוי חלוקה פנימית ופתיחת פתח בקיר חיצוני',
    gush: '1200',
    helka: '5'
  }
];

export const MOCK_APPLICATIONS: ApplicationPublication[] = [
    {
        id: 'app-1',
        city: 'רמת גן',
        request_id: '20240015',
        published_at: '2023-10-25T00:00:00Z',
        applicant_name: 'יוסי כהן יזמות בע"מ',
        description: 'בקשה להקלה בקו בניין אחורי עבור תוספת מרפסות',
        gush: '6122',
        helka: '45'
    },
    {
        id: 'app-2',
        city: 'הרצליה',
        request_id: '2024-0330',
        published_at: '2023-10-24T00:00:00Z',
        applicant_name: 'אפריקה ישראל מגורים',
        description: 'הריסת מבנה קיים והקמת בניין מגורים בן 9 קומות',
        gush: '6650',
        helka: '102'
    }
];

export const MOCK_PLANS: PlanPublication[] = [
    {
        id: 'plan-1',
        city: 'חולון',
        plan_number: '502-0987654',
        published_at: '2023-10-26T00:00:00Z',
        message_type: 'הודעה בדבר אישור תכנית',
        plan_goal: 'התחדשות עירונית מתחם קוגל',
        plan_main_points: 'שינוי ייעוד קרקע מאזור תעשייה למגורים ומסחר, קביעת זכויות בנייה ל-500 יח"ד.',
        gush: '7150',
        helka: 'All'
    },
    {
        id: 'plan-2',
        city: 'בת ים',
        plan_number: '502-111222',
        published_at: '2023-10-23T00:00:00Z',
        message_type: 'הודעה בדבר הפקדת תכנית',
        plan_goal: 'הרחבת דרך והסדרת צומת',
        plan_main_points: 'הפקעת שטחים לצורכי ציבור, שינוי קווי בניין.',
        gush: '7120',
        helka: '15, 16'
    }
];

export const MOCK_MEETING_DETAILS: Record<string, MeetingDetail> = {
  'a1b2c3d4-e5f6-7890-1234-567890abcdef': {
    ...MOCK_MEETINGS[0],
    meeting_id: '2023044',
    document_url: 'https://example.com/doc.pdf',
    created_at: '2023-10-16T10:00:00Z',
    raw: { source: 'scraper_v2', scraper_id: 111 },
    meeting_items: [
      {
        id: 'dec-1',
        request_id: '20191061 / תיק בניין 1581',
        decision: 'אושר בתנאים',
        status: 'אושרה הארכת תוקף היתר עד 03.11.2028',
        subject: 'שפרבר חיים, בת-ים (גוש 7124 חלקה 218 ועוד)',
        description: 'הארכת תוקף היתר בניה להקמת מבנה מגורים בן 33 קומות כולל קומת טכנית וקרקע מסחרית ושימושים ציבוריים, מבנה משרדים 7 קומות וחניון תת-קרקעי (סה"כ 187 יח"ד).',
        created_at: '2023-10-15T09:15:00Z',
        applicant: 'חלום בים בע"מ ע"י עמוס מימון',
        units: 187,
        raw: { original_text: 'אושר בכפוף להערות מהנדס העיר' }
      },
      {
        id: 'dec-2',
        request_id: '502-1410307 / בי/619',
        decision: 'נדחה',
        status: 'נדחתה במתכונתה הנוכחית; להמשיך ולעדכן בהתאם להנחיות התכנית הכוללת.',
        subject: 'שדרות העצמאות 34 ופינת רח\' עוזיאל (עוזיאל 2,4,6), בת-ים',
        description: 'תכנית פינוי-בינוי: הריסת 3 מבנים והקמת מבנה עירוב שימושים (קומת קרקע מסחרית ושב"צ + 8.5 קומות מגורים) ומגדל עירוב שימושים הכולל קומה ציבורית ומגדל מגורים בן 25 קומות; הקצאת שטחי ציבור והגדלת זכויות למגורים.',
        created_at: '2023-10-15T09:30:00Z',
        applicant: 'קבוצת יצחקי',
        raw: { original_text: 'נדחה עקב התנגדות דיירים' }
      }
    ]
  },
  'f1e2d3c4-b5a6-0987-6543-210987fedcba': {
     ...MOCK_MEETINGS[1],
     meeting_id: '2023042',
     document_url: 'https://jerusalem.muni.il/doc',
     meeting_items: [],
     raw: { note: 'No digital items parsed' }
  }
};

export const MOCK_PERMIT_DETAILS: Record<string, PermitDetail> = {
  '12345678-90ab-cdef-1234-567890abcdef': {
    ...MOCK_PERMITS[0],
    created_at: '2023-10-19T08:00:00Z',
    raw: { legacy_system_id: 998877, auditor: 'Moshe Cohen' },
    applicant_name: 'חברת בונים בע"מ',
    architect: 'דני אדריכל',
    total_area: '2500 sq meters'
  },
  'abcdef12-3456-7890-abcd-ef1234567890': {
    ...MOCK_PERMITS[1],
    created_at: '2023-10-17T09:20:00Z',
    raw: { import_date: '2023-10-20' }
  }
};