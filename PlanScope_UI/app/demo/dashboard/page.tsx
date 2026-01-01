'use client';

import React, { useState } from 'react';
import { useRouter } from '../../../utils/nextShim';
import { DemoLayout } from '../../../components/DemoShared';
import { Card, Chip, formatDate, EmptyState } from '../../../components/Shared';
import { DEMO_MEETINGS, DEMO_PERMITS, DEMO_APPLICATIONS, DEMO_PLANS } from '../../../services/demoData';
import { FeedType } from '../../../types';

const StatCard = ({ title, value, subtitle }: { title: string, value: string | number, subtitle: string }) => (
    <div className="bg-white p-6 rounded-xl border border-border shadow-sm flex flex-col items-center text-center hover:shadow-md transition-all duration-200">
        <h3 className="text-sm font-semibold text-textSecondary mb-3">{title}</h3>
        <div className="text-4xl font-black text-textPrimary mb-3 tracking-tight">{value}</div>
        <p className="text-xs text-gray-400 font-medium">{subtitle}</p>
    </div>
);

export default function DemoDashboardPage() {
    const { push } = useRouter();
    const [activeTab, setActiveTab] = useState<FeedType>('meetings');
    const [searchQuery, setSearchQuery] = useState('');

    const filterItem = (item: any) => {
        if (!searchQuery) return true;
        const q = searchQuery.toLowerCase();
        
        // Generic search over all fields
        const city = (item.city || '').toLowerCase();
        const id = (item.id || '').toLowerCase();
        
        if (activeTab === 'meetings') {
             const meetingId = (item.meeting_id || '').toLowerCase();
             return city.includes(q) || id.includes(q) || meetingId.includes(q);
        } else if (activeTab === 'permits') {
            const reqId = (item.request_id || '').toLowerCase();
            const essence = (item.essence || '').toLowerCase();
            return city.includes(q) || id.includes(q) || reqId.includes(q) || essence.includes(q);
        } else if (activeTab === 'applications') {
            const reqId = (item.request_id || '').toLowerCase();
            const applicant = (item.applicant_name || '').toLowerCase();
            const desc = (item.description || '').toLowerCase();
            return city.includes(q) || reqId.includes(q) || applicant.includes(q) || desc.includes(q);
        } else {
            // Plans
            const planNum = (item.plan_number || '').toLowerCase();
            const goal = (item.plan_goal || '').toLowerCase();
            return city.includes(q) || planNum.includes(q) || goal.includes(q);
        }
    };

    const renderControls = () => (
        <div className="flex bg-gray-200 p-1 rounded-lg self-start whitespace-nowrap overflow-x-auto max-w-full">
            <button onClick={() => setActiveTab('meetings')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${activeTab === 'meetings' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                ישיבות אחרונות
            </button>
            <button onClick={() => setActiveTab('permits')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${activeTab === 'permits' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                היתרים אחרונים
            </button>
            <button onClick={() => setActiveTab('applications')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${activeTab === 'applications' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                פרסומי בקשות
            </button>
             <button onClick={() => setActiveTab('plans')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all whitespace-nowrap ${activeTab === 'plans' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                פרסומי תכניות
            </button>
        </div>
    );

    // Calculate stats based on demo data
    const totalItems = DEMO_MEETINGS.length + DEMO_PERMITS.length + DEMO_APPLICATIONS.length + DEMO_PLANS.length;

    return (
        <DemoLayout backLink="/">
            <header className="mb-2">
                <h1 className="text-3xl font-bold text-textPrimary mb-1">לוח בקרה עירוני (דמו)</h1>
                <p className="text-textSecondary text-sm">הנתונים המוצגים הינם להמחשה בלבד ומתייחסים לעיר בת ים</p>
            </header>

             {/* Overview Section */}
             <div className="mb-8 animate-fade-in space-y-4">
                <div className="bg-white rounded-xl border border-border p-5 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div>
                        <h2 className="text-xl font-bold text-textPrimary mb-1">סקירה - בת ים</h2>
                        <p className="text-textSecondary text-sm">פעילות אחרונה במרחב התכנוני.</p>
                    </div>
                    <div className="flex flex-wrap gap-2">
                         <button className="px-4 py-1.5 rounded-lg border border-border text-sm font-semibold text-textSecondary hover:text-primary hover:border-primary/30 hover:bg-blue-50 transition-all bg-white shadow-sm">
                            7 ימים אחרונים
                        </button>
                    </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <StatCard title="מקורות" value="1" subtitle="עיריית בת ים" />
                    <StatCard title="עדכונים" value={totalItems} subtitle="במאגר הדמו" />
                    <StatCard title="היתרים חדשים" value={DEMO_PERMITS.length} subtitle="בדמו" />
                    <StatCard title="ישיבות" value={DEMO_MEETINGS.length} subtitle="בדמו" />
                </div>
            </div>

            {/* Controls */}
            <div className="flex flex-col md:flex-row gap-4 mb-6 sticky top-16 z-40 bg-background/95 backdrop-blur py-2">
                {renderControls()}

                <div className="flex-grow">
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="חפש בנתוני הדמו..."
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            className="w-full pl-4 pr-10 py-2.5 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all shadow-sm"
                        />
                        <svg className="absolute left-3 top-3 w-5 h-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    </div>
                </div>
            </div>

            {/* Content Feed */}
            <div className="grid gap-4">
                {activeTab === 'meetings' && DEMO_MEETINGS.filter(filterItem).map(meeting => (
                        <Card 
                        key={meeting.id} 
                        onClick={() => push(`/demo/meetings/${meeting.id}`)}
                        className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group cursor-pointer hover:border-blue-300 transition-colors"
                    >
                        <div className="flex-grow">
                            <div className="flex items-center gap-2 mb-1">
                                <h3 className="text-lg font-bold text-textPrimary group-hover:text-primary transition-colors">
                                    ישיבה מס׳: {meeting.meeting_id || 'ללא מספר'}
                                </h3>
                                <Chip label={`${meeting.decisions_count} החלטות`} color="blue" />
                            </div>
                            <div className="flex items-center gap-3 text-sm text-textSecondary">
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    {formatDate(meeting.meeting_date)}
                                </span>
                                <span className="text-gray-300">|</span>
                                <span>{meeting.city}</span>
                            </div>
                        </div>
                        <div className="text-primary opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 rotate-180">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                            </svg>
                        </div>
                    </Card>
                ))}

                {activeTab === 'permits' && DEMO_PERMITS.filter(filterItem).map(permit => (
                        <Card 
                        key={permit.id} 
                        onClick={() => push(`/demo/permits/${permit.id}`)}
                        className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group cursor-pointer hover:border-blue-300 transition-colors"
                    >
                        <div className="flex-grow w-full md:w-auto">
                            <div className="flex items-center flex-wrap gap-2 mb-2">
                                <h3 className="text-lg font-bold text-textPrimary group-hover:text-primary transition-colors">
                                    היתר מס׳: {permit.request_id || 'ללא מספר'}
                                </h3>
                                {permit.request_type && <Chip label={permit.request_type} color="orange" />}
                                {permit.gush && permit.helka && (
                                    <Chip label={`גוש ${permit.gush} / חלקה ${permit.helka}`} className="bg-gray-50 text-gray-500 border-gray-100" />
                                )}
                            </div>
                            <p className="text-sm text-textPrimary mb-2 line-clamp-1 max-w-2xl">{permit.essence || 'אין תיאור מהות'}</p>
                            <div className="flex items-center gap-3 text-sm text-textSecondary">
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    {formatDate(permit.permit_date)}
                                </span>
                                <span className="text-gray-300">|</span>
                                <span>{permit.city}</span>
                            </div>
                        </div>
                    </Card>
                ))}
                
                {activeTab === 'applications' && DEMO_APPLICATIONS.filter(filterItem).map(app => (
                        <Card 
                        key={app.id} 
                        onClick={() => push(`/demo/applications/${app.id}`)}
                        className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group cursor-pointer hover:border-purple-300 transition-colors"
                    >
                        <div className="flex-grow w-full md:w-auto">
                            <div className="flex items-center flex-wrap gap-2 mb-2">
                                <Chip label="פרסום בקשה" color="purple" />
                                <h3 className="text-lg font-bold text-textPrimary group-hover:text-primary transition-colors">
                                    בקשה מס׳: {app.request_id}
                                </h3>
                                {app.gush && app.helka && (
                                    <Chip label={`גוש ${app.gush} / חלקה ${app.helka}`} className="bg-gray-50 text-gray-500 border-gray-100" />
                                )}
                            </div>
                            <div className="mb-2">
                                    <span className="text-xs font-semibold text-gray-500 block mb-1">מבקש: {app.applicant_name}</span>
                                    <p className="text-sm text-textPrimary line-clamp-1 max-w-2xl">{app.description}</p>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-textSecondary">
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    {formatDate(app.published_at)}
                                </span>
                                <span className="text-gray-300">|</span>
                                <span>{app.city}</span>
                            </div>
                        </div>
                    </Card>
                ))}

                 {activeTab === 'plans' && DEMO_PLANS.filter(filterItem).map(plan => (
                        <Card 
                        key={plan.id} 
                        onClick={() => push(`/demo/plans/${plan.id}`)}
                        className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group cursor-pointer hover:border-green-300 transition-colors"
                    >
                        <div className="flex-grow w-full md:w-auto">
                            <div className="flex items-center flex-wrap gap-2 mb-2">
                                <Chip label={plan.message_type} color="green" />
                                {plan.plan_number && <span className="text-sm font-mono text-gray-500">{plan.plan_number}</span>}
                                {plan.gush && (
                                    <Chip label={`גוש ${plan.gush} ${plan.helka ? `/ חלקה ${plan.helka}` : ''}`} className="bg-gray-50 text-gray-500 border-gray-100" />
                                )}
                            </div>
                            <div className="mb-2">
                                    <h3 className="text-lg font-bold text-textPrimary mb-1 group-hover:text-primary transition-colors">{plan.plan_goal}</h3>
                                    <p className="text-sm text-textSecondary line-clamp-2 max-w-2xl">{plan.plan_main_points}</p>
                            </div>
                            <div className="flex items-center gap-3 text-sm text-textSecondary">
                                <span className="flex items-center gap-1">
                                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                    {formatDate(plan.published_at)}
                                </span>
                                <span className="text-gray-300">|</span>
                                <span>{plan.city}</span>
                            </div>
                        </div>
                    </Card>
                ))}
            </div>
        </DemoLayout>
    );
}