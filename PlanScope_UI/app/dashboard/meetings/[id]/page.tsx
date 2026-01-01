'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from '../../../../utils/nextShim';
import { api } from '../../../../services/api';
import { MeetingDetail } from '../../../../types';
import { 
    PageLayout, Card, Chip, KeyValueGrid, 
    CopyButton, formatDate, LoadingState, EmptyState, WatchlistToggle 
} from '../../../../components/Shared';

const MeetingDetailPage = () => {
    const params = useParams();
    const id = params?.id as string;
    const [meeting, setMeeting] = useState<MeetingDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [decisionSearch, setDecisionSearch] = useState('');

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        api.meetings.getById(id)
            .then(data => setMeeting(data))
            .catch(err => setError('שגיאה בטעינת הישיבה'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <PageLayout><LoadingState /></PageLayout>;
    if (error || !meeting) return (
        <PageLayout backLink="/dashboard">
            <EmptyState message={error || "ישיבה לא נמצאה"} />
        </PageLayout>
    );

    const filteredItems = (meeting.meeting_items || []).filter(item => 
        (item.request_id || '').includes(decisionSearch) ||
        (item.description || '').includes(decisionSearch) ||
        (item.subject || '').includes(decisionSearch)
    );

    return (
        <PageLayout backLink="/dashboard">
            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">ישיבה</h1>
                        {meeting.meeting_id && (
                            <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-lg text-xl font-bold border border-gray-200 shadow-sm">
                                #{meeting.meeting_id}
                            </span>
                        )}
                        <WatchlistToggle id={meeting.id} type="meeting" className="mr-2" />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(meeting.meeting_date)}
                        </span>
                        <span className="text-gray-300">|</span>
                        <CopyButton text={meeting.id} label="UUID" />
                        {meeting.document_url && (
                             <>
                                <span className="text-gray-300">|</span>
                                <a 
                                    href={meeting.document_url} 
                                    target="_blank" 
                                    rel="noreferrer" 
                                    className="inline-flex items-center gap-1.5 bg-primary hover:bg-primaryHover text-white px-3 py-1 rounded-full font-medium transition-colors shadow-sm text-xs"
                                >
                                    <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                                    פתח מסמך PDF
                                </a>
                             </>
                        )}
                    </div>
                </div>
            </div>

            {/* Metadata Card */}
            <Card className="p-6">
                <div className="mb-4">
                    <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטי ישיבה</h2>
                    <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                </div>
                <KeyValueGrid 
                    data={meeting} 
                    excludeKeys={['id', 'meeting_items', 'raw']} 
                />
            </Card>

            {/* Decisions List */}
            <div className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                    <h2 className="text-xl font-bold text-textPrimary flex items-center gap-2">
                        החלטות ונושאים
                        <Chip label={meeting.meeting_items?.length || 0} color="blue" />
                    </h2>
                    <div className="relative max-w-xs w-full">
                        <input
                            type="text"
                            placeholder="חיפוש..."
                            value={decisionSearch}
                            onChange={(e) => setDecisionSearch(e.target.value)}
                            className="w-full pl-4 pr-10 py-2 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all text-sm"
                        />
                        <svg className="absolute left-3 top-2.5 w-4 h-4 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" /></svg>
                    </div>
                </div>

                {filteredItems.length === 0 ? (
                    <Card className="p-12 text-center text-textSecondary bg-gray-50 border-dashed">
                        {meeting.meeting_items?.length === 0 
                            ? "אין החלטות זמינות לישיבה זו" 
                            : "לא נמצאו תוצאות בסינון הנוכחי"}
                    </Card>
                ) : (
                    <div className="grid grid-cols-1 gap-6">
                        {filteredItems.map((item, idx) => {
                            // Determine status color
                            const status = item.status || item.decision || '';
                            const isApproved = status.includes('אושר') || status.includes('אושרה');
                            const isDenied = status.includes('נדחה') || status.includes('נדחתה');
                            
                            return (
                                <Card key={idx} className="p-6 relative overflow-visible border hover:border-blue-200 transition-all">
                                    <div className="absolute top-0 right-0 left-0 h-1 bg-gradient-to-r from-gray-200 via-gray-100 to-gray-200" />
                                    
                                    <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-3">
                                        <div>
                                            {item.decision && (
                                                <span className="text-sm font-semibold text-gray-400 mb-1 block">
                                                    {item.decision}
                                                </span>
                                            )}
                                            <h3 className="text-xl font-bold text-textPrimary" dir="ltr">
                                                {item.request_id ? `בקשה ${item.request_id}` : 'ללא מספר בקשה'}
                                            </h3>
                                        </div>
                                        <div className="flex items-center gap-2">
                                           {/* Decision Watchlist Toggle (Generic for now as item doesn't always have ID, using index fallback logic if needed) */}
                                           {item.id && <WatchlistToggle id={item.id} type="decision" className="bg-white border shadow-sm" />}
                                        </div>
                                    </div>

                                    <div className="mb-4">
                                        <p className="text-base text-gray-800 font-medium leading-relaxed">
                                            {item.subject}
                                        </p>
                                    </div>

                                    {item.description && (
                                        <div className="mb-5 bg-gray-50 p-4 rounded-lg border border-gray-100 text-sm leading-relaxed text-gray-700">
                                            {item.description}
                                        </div>
                                    )}

                                    {/* Status Bar */}
                                    <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 pt-3 mt-auto">
                                        <div className={`px-3 py-1 rounded-full text-sm font-bold border shadow-sm ${isApproved ? 'bg-green-50 text-green-700 border-green-200' : isDenied ? 'bg-red-50 text-red-700 border-red-200' : 'bg-gray-100 text-gray-700'}`}>
                                            סטטוס: {item.status || item.decision || 'לא ידוע'}
                                        </div>
                                        
                                        {item.applicant && (
                                            <div className="px-3 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-600">
                                                מבקש: {item.applicant}
                                            </div>
                                        )}
                                        
                                        {item.units && (
                                            <div className="px-3 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-600">
                                                יח"ד: {item.units}
                                            </div>
                                        )}

                                        {item.valid_until && (
                                             <div className="px-3 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-600">
                                                {item.valid_until}
                                            </div>
                                        )}
                                    </div>
                                </Card>
                            );
                        })}
                    </div>
                )}
            </div>
        </PageLayout>
    );
};

export default MeetingDetailPage;