'use client';

import React, { useEffect, useState } from 'react';
import { useParams } from '../../../../utils/nextShim';
import { api } from '../../../../services/api';
import { PlanPublication } from '../../../../types';
import { 
    PageLayout, Card, Chip, KeyValueGrid, 
    CopyButton, formatDate, LoadingState, EmptyState, WatchlistToggle 
} from '../../../../components/Shared';

const PlanDetailPage = () => {
    const params = useParams();
    const id = params?.id as string;
    const [plan, setPlan] = useState<PlanPublication | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!id) return;
        setLoading(true);
        api.plans.getById(id)
            .then(data => setPlan(data))
            .catch(err => setError('שגיאה בטעינת התוכנית'))
            .finally(() => setLoading(false));
    }, [id]);

    if (loading) return <PageLayout><LoadingState /></PageLayout>;
    if (error || !plan) return (
        <PageLayout backLink="/dashboard">
            <EmptyState message={error || "תוכנית לא נמצאה"} />
        </PageLayout>
    );

    return (
        <PageLayout backLink="/dashboard">
             <div className="flex flex-col gap-4">
                <div>
                    <div className="flex items-center gap-3">
                        <Chip label={plan.message_type} color="green" />
                        <WatchlistToggle id={plan.id} type="plan" />
                    </div>
                    <h1 className="text-3xl font-bold text-textPrimary mt-2">{plan.plan_goal}</h1>
                    <div className="flex flex-wrap items-center gap-3 mt-2 text-textSecondary text-sm">
                        <span className="flex items-center gap-1">
                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                            {formatDate(plan.published_at)}
                        </span>
                        <span className="text-gray-300">|</span>
                        <span>{plan.city}</span>
                        <span className="text-gray-300">|</span>
                        <CopyButton text={plan.id} label="UUID" />
                    </div>
                </div>
            </div>

            {/* Main Points */}
            <Card className="p-6 bg-green-50/50 border-green-100">
                <h2 className="text-lg font-bold text-green-900 mb-2">עיקרי התוכנית</h2>
                <p className="text-lg text-gray-800 leading-relaxed">
                    {plan.plan_main_points}
                </p>
            </Card>

            {/* Main Details */}
            <Card className="p-6">
                <div className="mb-6">
                    <h2 className="text-lg font-semibold text-textPrimary mb-1">פרטי התוכנית</h2>
                    <div className="h-0.5 w-10 bg-primary rounded-full"></div>
                </div>

                <KeyValueGrid 
                    data={plan} 
                    excludeKeys={['id', 'plan_main_points', 'plan_goal', 'raw']} 
                />
            </Card>
        </PageLayout>
    );
};

export default PlanDetailPage;