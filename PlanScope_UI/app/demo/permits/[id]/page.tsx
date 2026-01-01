'use client';

import React from 'react';
import { useParams } from '../../../../utils/nextShim';
import { DEMO_PERMIT_DETAILS } from '../../../../services/demoData';
import { DemoLayout } from '../../../../components/DemoShared';
import { Card, Chip, KeyValueGrid, CopyButton, formatDate, EmptyState, WatchlistToggle } from '../../../../components/Shared';

export default function DemoPermitDetailPage() {
    const params = useParams();
    const id = params?.id as string;
    const permit = DEMO_PERMIT_DETAILS[id];

    if (!permit) return (
        <DemoLayout backLink="/demo/dashboard">
            <EmptyState message="היתר דמו לא נמצא" />
        </DemoLayout>
    );

    return (
        <DemoLayout backLink="/demo/dashboard">
             <div className="flex flex-col gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">היתר בנייה (דמו): {permit.city}</h1>
                        <WatchlistToggle id={permit.id} type="permit" />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(permit.permit_date)}
                        </span>
                        <span className="font-medium">בקשה: {permit.request_id}</span>
                    </div>
                </div>
            </div>

            {permit.essence && (
                <Card className="p-6 bg-gradient-to-br from-white to-blue-50/30 border-t-4 border-t-primary">
                    <h2 className="text-lg font-bold text-primary mb-3 flex items-center gap-2">
                        תקציר הפרויקט
                    </h2>
                    <p className="text-lg text-gray-800 leading-relaxed">
                        {permit.essence}
                    </p>
                </Card>
            )}

            <Card className="p-6">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטי היתר</h2>
                        <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                    </div>
                    {permit.request_type && <Chip label={permit.request_type} color="orange" className="text-sm" />}
                </div>
                <KeyValueGrid data={permit} excludeKeys={['id', 'raw', 'essence', 'license_id']} />
            </Card>
        </DemoLayout>
    );
}