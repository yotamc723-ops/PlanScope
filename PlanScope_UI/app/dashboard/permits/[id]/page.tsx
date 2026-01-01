'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from '../../../../utils/nextShim';
import { api } from '../../../../services/api';
import { PermitDetail } from '../../../../types';
import { 
    PageLayout, Card, Chip, KeyValueGrid, 
    CopyButton, formatDate, LoadingState, EmptyState, WatchlistToggle 
} from '../../../../components/Shared';

const PermitDetailPage = () => {
    const params = useParams();
    const id = params?.id as string;
    const [permit, setPermit] = useState<PermitDetail | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        api.permits.getById(id)
            .then(data => setPermit(data))
            .catch(err => setError('שגיאה בטעינת ההיתר'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <PageLayout><LoadingState /></PageLayout>;
    if (error || !permit) return (
        <PageLayout backLink="/dashboard">
            <EmptyState message={error || "היתר לא נמצא"} />
        </PageLayout>
    );

    return (
        <PageLayout backLink="/dashboard">
             {/* Header */}
             <div className="flex flex-col gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">היתר בנייה: {permit.city}</h1>
                        <WatchlistToggle id={permit.id} type="permit" />
                    </div>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(permit.permit_date)}
                        </span>
                        {permit.request_id && (
                            <>
                                <span className="text-gray-300">|</span>
                                <span className="font-medium">בקשה: {permit.request_id}</span>
                            </>
                        )}
                        <span className="text-gray-300">|</span>
                        <CopyButton text={permit.id} label="UUID" />
                    </div>
                </div>
            </div>

            {/* Project Summary Block */}
            {permit.essence && (
                <Card className="p-6 bg-gradient-to-br from-white to-blue-50/30 border-t-4 border-t-primary">
                    <h2 className="text-lg font-bold text-primary mb-3 flex items-center gap-2">
                        <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" /></svg>
                        תקציר הפרויקט
                    </h2>
                    <p className="text-lg text-gray-800 leading-relaxed">
                        {permit.essence}
                    </p>
                </Card>
            )}

            {/* Main Details Card */}
            <Card className="p-6">
                <div className="mb-6 flex items-center justify-between">
                    <div>
                        <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטי היתר</h2>
                        <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                    </div>
                    {permit.request_type && (
                         <Chip label={permit.request_type} color="orange" className="text-sm" />
                    )}
                </div>

                <KeyValueGrid 
                    data={permit} 
                    excludeKeys={['id', 'raw', 'essence', 'license_id']} 
                />
            </Card>
        </PageLayout>
    );
};

export default PermitDetailPage;