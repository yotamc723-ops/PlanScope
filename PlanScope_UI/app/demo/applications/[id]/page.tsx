'use client';

import React from 'react';
import { useParams } from '../../../../utils/nextShim';
import { DEMO_APPLICATION_DETAILS } from '../../../../services/demoData';
import { DemoLayout } from '../../../../components/DemoShared';
import { Card, Chip, KeyValueGrid, CopyButton, formatDate, EmptyState, WatchlistToggle } from '../../../../components/Shared';

export default function DemoApplicationDetailPage() {
    const params = useParams();
    const id = params?.id as string;
    const app = DEMO_APPLICATION_DETAILS[id];

    if (!app) return (
        <DemoLayout backLink="/demo/dashboard">
            <EmptyState message="בקשת דמו לא נמצאה" />
        </DemoLayout>
    );

    return (
        <DemoLayout backLink="/demo/dashboard">
             <div className="flex flex-col gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">פרסום בקשה (דמו)</h1>
                        <WatchlistToggle id={app.id} type="application" />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(app.published_at)}
                        </span>
                        <span className="text-gray-300">|</span>
                        <span>{app.city}</span>
                        <span className="text-gray-300">|</span>
                        <CopyButton text={app.id} label="UUID" />
                    </div>
                </div>
            </div>

            {/* Description */}
            <Card className="p-6 bg-purple-50/50 border-purple-100">
                <h2 className="text-lg font-bold text-purple-900 mb-2">תיאור הבקשה</h2>
                <p className="text-lg text-gray-800 leading-relaxed">
                    {app.description}
                </p>
            </Card>

            {/* Main Details */}
            <Card className="p-6">
                <div className="mb-6">
                    <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטים טכניים</h2>
                    <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                </div>

                <KeyValueGrid 
                    data={app} 
                    excludeKeys={['id', 'description', 'raw']} 
                />
            </Card>
        </DemoLayout>
    );
}