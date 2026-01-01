'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from '../../utils/nextShim';
import { api } from '../../services/api';
import { PageLayout, Card, Chip, formatDate, LoadingState, EmptyState, WatchlistToggle } from '../../components/Shared';
import { PaidRoute } from '../../components/PaidRoute';

interface WatchedItem {
    id: string;
    type: string;
    data: any;
}

export default function WatchlistPage() {
    const { push } = useRouter();
    const [items, setItems] = useState<WatchedItem[]>([]);
    const [loading, setLoading] = useState(true);
    const [filter, setFilter] = useState<'all' | 'meeting' | 'permit' | 'application' | 'plans'>('all');

    const loadWatchlist = async () => {
        setLoading(true);
        try {
            const saved = JSON.parse(localStorage.getItem('municipal_watchlist') || '[]');
            
            if (saved.length === 0) {
                setItems([]);
                setLoading(false);
                return;
            }

            // Fetch details for each watched item
            const results = await Promise.allSettled(
                saved.map(async (item: any) => {
                    if (item.type === 'meeting') {
                        const data = await api.meetings.getById(item.id);
                        return { ...item, data };
                    } else if (item.type === 'permit') {
                        const data = await api.permits.getById(item.id);
                        return { ...item, data };
                    } else if (item.type === 'application') {
                         const data = await api.applications.getById(item.id);
                         return { ...item, data };
                    } else if (item.type === 'plan') {
                        const data = await api.plans.getById(item.id);
                        return { ...item, data };
                    }
                    return null;
                })
            );

            // Filter out failed requests and nulls
            const successItems = results
                .filter(r => r.status === 'fulfilled')
                .map(r => (r as PromiseFulfilledResult<WatchedItem | null>).value)
                .filter(Boolean) as WatchedItem[];
            
            setItems(successItems);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadWatchlist();
        const handleUpdate = () => loadWatchlist();
        window.addEventListener('watchlist-updated', handleUpdate);
        return () => window.removeEventListener('watchlist-updated', handleUpdate);
    }, []);

    const filteredItems = items
        .filter(item => {
            if (filter === 'all') return item.type !== 'plan'; // Plans are separate
            if (filter === 'plans') return item.type === 'plan';
            return item.type === filter;
        })
        .sort((a, b) => {
             // Sort newest up
             const getTime = (itm: any) => new Date(itm.data.meeting_date || itm.data.permit_date || itm.data.published_at || 0).getTime();
             return getTime(b) - getTime(a);
        });

    return (
        <PaidRoute>
        <PageLayout>
            <header className="mb-2">
                <h1 className="text-3xl font-bold text-textPrimary mb-1">רשימת מעקב</h1>
                <p className="text-textSecondary text-sm">התראות ועדכונים עבור פריטים שסימנת</p>
            </header>

            {/* Filter Controls */}
            <div className="flex bg-gray-100 p-1 rounded-lg self-start whitespace-nowrap overflow-x-auto w-full md:w-auto mb-6">
                <button onClick={() => setFilter('all')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${filter === 'all' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                    כללי (ישיבות/היתרים/בקשות)
                </button>
                <button onClick={() => setFilter('plans')} className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${filter === 'plans' ? 'bg-white text-primary shadow-sm' : 'text-textSecondary hover:text-textPrimary'}`}>
                    תוכניות (נפרד)
                </button>
            </div>

            {loading ? (
                <LoadingState />
            ) : filteredItems.length === 0 ? (
                <EmptyState 
                    message={filter === 'all' ? "לא נוספו פריטים כלליים" : "לא נוספו תוכניות"} 
                    icon={<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-10 h-10"><path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.563.045.797.77.373 1.137l-4.204 3.602a.563.563 0 00-.172.543l1.205 5.312a.563.563 0 01-.817.616l-4.632-2.825a.563.563 0 00-.594 0l-4.632 2.825a.563.563 0 01-.817-.616l1.205-5.312a.563.563 0 00-.172-.543L3.41 10.535c-.424-.367-.19-1.092.373-1.137l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" /></svg>}
                />
            ) : (
                <div className="grid gap-4">
                    {filteredItems.map(item => {
                        const data = item.data;
                        const type = item.type;
                        
                        let path = '';
                        let label = '';
                        let color: any = 'gray';
                        let title = '';
                        let date = '';
                        
                        if (type === 'meeting') {
                            path = `/dashboard/meetings/${data.id}`;
                            label = 'ישיבה'; color = 'blue';
                            title = `ישיבה מס׳: ${data.meeting_id}`;
                            date = data.meeting_date;
                        } else if (type === 'permit') {
                            path = `/dashboard/permits/${data.id}`;
                            label = 'היתר'; color = 'orange';
                            title = `היתר מס׳: ${data.request_id}`;
                            date = data.permit_date;
                        } else if (type === 'application') {
                            path = `/dashboard/applications/${data.id}`;
                            label = 'בקשה'; color = 'purple';
                            title = `בקשה מס׳: ${data.request_id}`;
                            date = data.published_at;
                        } else if (type === 'plan') {
                            path = `/dashboard/plans/${data.id}`;
                            label = 'תוכנית'; color = 'green';
                            title = data.plan_goal || data.message_type;
                            date = data.published_at;
                        }

                        return (
                            <Card key={item.id} onClick={() => push(path)} className="p-5 flex flex-col md:flex-row items-start md:items-center justify-between gap-4 group cursor-pointer hover:border-blue-300 transition-colors">
                                <div className="flex-grow w-full md:w-auto">
                                    <div className="flex items-center gap-2 mb-2">
                                        <Chip label={label} color={color} />
                                        <h3 className="text-lg font-bold text-textPrimary group-hover:text-primary transition-colors">{title}</h3>
                                    </div>
                                    <div className="flex items-center gap-3 text-sm text-textSecondary">
                                        <span className="flex items-center gap-1">
                                            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" /></svg>
                                            {formatDate(date)}
                                        </span>
                                        <span className="text-gray-300">|</span>
                                        <span>{data.city}</span>
                                    </div>
                                </div>
                                <div className="flex items-center gap-3">
                                    <WatchlistToggle id={data.id} type={type as any} />
                                    <div className="text-primary opacity-0 group-hover:opacity-100 transition-opacity transform translate-x-2 group-hover:translate-x-0 hidden md:block">
                                        <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-6 h-6 rotate-180"><path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" /></svg>
                                    </div>
                                </div>
                            </Card>
                        );
                    })}
                </div>
            )}
        </PageLayout>
        </PaidRoute>
    );
}