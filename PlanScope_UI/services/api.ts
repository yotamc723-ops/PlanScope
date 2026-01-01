import { MeetingSummary, MeetingDetail, PermitSummary, PermitDetail, ApplicationPublication, PlanPublication } from '../types';
import { MOCK_MEETINGS, MOCK_PERMITS, MOCK_MEETING_DETAILS, MOCK_PERMIT_DETAILS, MOCK_APPLICATIONS, MOCK_PLANS } from './mockData';

// Simulate network delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const api = {
  meetings: {
    recent: async (): Promise<MeetingSummary[]> => {
      await delay(600);
      return [...MOCK_MEETINGS];
    },
    getById: async (id: string): Promise<MeetingDetail> => {
      await delay(400);
      const meeting = MOCK_MEETING_DETAILS[id];
      if (!meeting) {
        // Fallback for demo purposes if ID not in mock map but valid format
        const summary = MOCK_MEETINGS.find(m => m.id === id);
        if (summary) {
            return { ...summary, meeting_items: [], raw: { note: 'Mock detailed data generated' } };
        }
        throw new Error('Meeting not found');
      }
      return meeting;
    }
  },
  permits: {
    recent: async (): Promise<PermitSummary[]> => {
      await delay(600);
      return [...MOCK_PERMITS];
    },
    getById: async (id: string): Promise<PermitDetail> => {
      await delay(400);
      const permit = MOCK_PERMIT_DETAILS[id];
      if (!permit) {
         const summary = MOCK_PERMITS.find(p => p.id === id);
         if (summary) {
             return { ...summary, raw: { note: 'Mock detailed data generated' } };
         }
        throw new Error('Permit not found');
      }
      return permit;
    }
  },
  applications: {
    recent: async (): Promise<ApplicationPublication[]> => {
        await delay(500);
        return [...MOCK_APPLICATIONS];
    },
    getById: async (id: string): Promise<ApplicationPublication> => {
        await delay(300);
        const app = MOCK_APPLICATIONS.find(a => a.id === id);
        if (!app) throw new Error('Application not found');
        return app;
    }
  },
  plans: {
    recent: async (): Promise<PlanPublication[]> => {
        await delay(500);
        return [...MOCK_PLANS];
    },
    getById: async (id: string): Promise<PlanPublication> => {
        await delay(300);
        const plan = MOCK_PLANS.find(p => p.id === id);
        if (!plan) throw new Error('Plan not found');
        return plan;
    }
  }
};