'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from '../../../../utils/nextShim';
import { api } from '../../../../services/api';
import { ApplicationPublication } from '../../../../types';
import { 
    PageLayout, Card, Chip, KeyValueGrid, 
    CopyButton, formatDate, LoadingState, EmptyState, WatchlistToggle 
} from '../../../../components/Shared';

const ApplicationDetailPage = () => {
    const params = useParams();
    const id = params?.id as string;
    const [app, setApp] = useState<ApplicationPublication | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        api.applications.getById(id)
            .then(data => setApp(data))
            .catch(err => setError('שגיאה בטעינת הבקשה'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <PageLayout><LoadingState /></PageLayout>;
    if (error || !app) return (
        <PageLayout backLink="/dashboard">
            <EmptyState message={error || "בקשה לא נמצאה"} />
        </PageLayout>
    );

    return (
        <PageLayout backLink="/dashboard">
             <div className="flex flex-col gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <h1 className="text-3xl font-bold text-textPrimary">פרסום בקשה</h1>
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
        </PageLayout>
    );
};

export default ApplicationDetailPage;