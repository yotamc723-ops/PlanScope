// Data models based on the API contracts

export interface MeetingSummary {
  id: string; // uuid
  city: string;
  meeting_date: string | null;
  decisions_count: number;
  meeting_id?: string;
}

export interface MeetingDetail extends MeetingSummary {
  document_url?: string;
  created_at?: string;
  raw?: any;
  meeting_items: MeetingItem[];
  [key: string]: any;
}

export interface MeetingItem {
  id?: string; // added for tracking
  request_id?: string;
  decision?: string;
  subject?: string;
  created_at?: string;
  raw?: any;
  status?: string; // from screenshot
  description?: string; // from screenshot
  units?: number; // from screenshot
  valid_until?: string; // from screenshot
  applicant?: string; // from screenshot
  [key: string]: any;
}

export interface PermitSummary {
  id: string; // uuid
  city: string;
  request_id?: string;
  permit_date: string | null;
  request_type?: string;
  essence?: string;
  gush?: string;
  helka?: string;
}

export interface PermitDetail extends PermitSummary {
  created_at?: string;
  raw?: any;
  [key: string]: any;
}

// New Types

export interface ApplicationPublication {
  id: string;
  city: string;
  request_id: string; // Number of application
  published_at: string | null;
  applicant_name: string;
  description: string;
  gush?: string;
  helka?: string;
  [key: string]: any;
}

export interface PlanPublication {
  id: string;
  city: string;
  plan_number?: string;
  published_at: string | null;
  message_type: string; // e.g. "הודעה בדבר הפקדה"
  plan_goal?: string;
  plan_main_points?: string;
  gush?: string;
  helka?: string;
  [key: string]: any;
}

export type FeedType = 'meetings' | 'permits' | 'applications' | 'plans';

export interface ApiResponse<T> {
  data: T;
  error?: string;
}