'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from '../../../../utils/nextShim';
import { DEMO_MEETING_DETAILS } from '../../../../services/demoData';
import { DemoLayout } from '../../../../components/DemoShared';
import { Card, Chip, KeyValueGrid, CopyButton, formatDate, EmptyState, WatchlistToggle } from '../../../../components/Shared';

export default function DemoMeetingDetailPage() {
    const params = useParams();
    const id = params?.id as string;
    const meeting = DEMO_MEETING_DETAILS[id];

    if (!meeting) return (
        <DemoLayout backLink="/demo/dashboard">
            <EmptyState message="ישיבת דמו לא נמצאה" />
        </DemoLayout>
    );

    return (
        <DemoLayout backLink="/demo/dashboard">
            <div className="flex flex-col md:flex-row md:items-end md:justify-between gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">ישיבה (דמו)</h1>
                        <span className="bg-gray-100 text-gray-800 px-3 py-1 rounded-lg text-xl font-bold border border-gray-200 shadow-sm">
                            #{meeting.meeting_id}
                        </span>
                        <WatchlistToggle id={meeting.id} type="meeting" className="mr-2" />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(meeting.meeting_date)}
                        </span>
                        <span className="text-gray-300">|</span>
                        <span>{meeting.city}</span>
                    </div>
                </div>
            </div>

            <Card className="p-6">
                <div className="mb-4">
                    <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטי ישיבה</h2>
                    <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                </div>
                <KeyValueGrid data={meeting} excludeKeys={['id', 'meeting_items', 'raw']} />
            </Card>

            <div className="space-y-4">
                <h2 className="text-xl font-bold text-textPrimary flex items-center gap-2">
                    החלטות ונושאים
                    <Chip label={meeting.meeting_items?.length || 0} color="blue" />
                </h2>

                <div className="grid grid-cols-1 gap-6">
                    {meeting.meeting_items.map((item, idx) => {
                        const isApproved = (item.status || '').includes('אושר');
                        return (
                            <Card key={idx} className="p-6 relative overflow-visible border hover:border-blue-200 transition-all">
                                <div className="flex flex-col md:flex-row justify-between items-start gap-4 mb-3">
                                    <div>
                                        <h3 className="text-xl font-bold text-textPrimary" dir="ltr">
                                            {item.request_id || 'ללא מספר בקשה'}
                                        </h3>
                                    </div>
                                    <WatchlistToggle id={`demo-dec-${idx}`} type="decision" className="bg-white border shadow-sm" />
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

                                <div className="flex flex-wrap items-center gap-3 border-t border-gray-100 pt-3 mt-auto">
                                    <div className={`px-3 py-1 rounded-full text-sm font-bold border shadow-sm ${isApproved ? 'bg-green-50 text-green-700 border-green-200' : 'bg-gray-100 text-gray-700'}`}>
                                        סטטוס: {item.status || item.decision || 'לא ידוע'}
                                    </div>
                                    {item.applicant && <div className="px-3 py-1 rounded-full bg-white border border-gray-200 text-xs text-gray-600">מבקש: {item.applicant}</div>}
                                </div>
                            </Card>
                        );
                    })}
                </div>
            </div>
        </DemoLayout>
    );
}