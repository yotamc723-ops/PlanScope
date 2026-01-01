'use client';

import React from 'react';
import { useAuth, PageLayout, Card, Chip, LoadingState } from '../../components/Shared';
import { ProtectedRoute } from '../../components/ProtectedRoute';
import { useRouter } from '../../utils/nextShim';

export default function MyPlanPage() {
    const { user } = useAuth();
    const { push } = useRouter();

    return (
        <ProtectedRoute>
        <PageLayout>
            <header className="mb-6">
                <h1 className="text-3xl font-bold text-textPrimary mb-1">התוכנית שלי</h1>
                <p className="text-textSecondary text-sm">ניהול מנוי ופרטי תשלום</p>
            </header>

            <div className="grid md:grid-cols-3 gap-6">
                {/* Current Plan Card */}
                <Card className="col-span-2 p-8 border-t-4 border-t-primary relative">
                    <div className="flex justify-between items-start mb-6">
                        <div>
                            <div className="flex items-center gap-3 mb-2">
                                <h2 className="text-2xl font-bold text-textPrimary">מנוי {user?.plan || 'Free'}</h2>
                                <Chip label="פעיל" color="green" />
                            </div>
                            <p className="text-textSecondary">
                                {user?.plan === 'Pro' 
                                    ? 'גישה מלאה לכל הנתונים, חיפוש מתקדם והתראות.' 
                                    : user?.plan === 'Enterprise'
                                    ? 'גישה ארגונית מלאה עם תמיכה מועדפת.'
                                    : 'חבילה בסיסית. שדרג כדי לקבל גישה מלאה.'}
                            </p>
                        </div>
                        <div className="text-right">
                             <div className="text-3xl font-black text-textPrimary">
                                {user?.plan === 'Free' ? '0' : user?.plan === 'Enterprise' ? '199' : '39'} ₪
                             </div>
                             <div className="text-sm text-textSecondary">לחודש</div>
                        </div>
                    </div>

                    {/* Billing info - Only shown for paid users */}
                    {user?.plan !== 'Free' && (
                        <div className="border-t border-b border-gray-100 py-6 my-6 space-y-4">
                            <div className="flex justify-between items-center">
                                <span className="text-textSecondary">חיוב הבא:</span>
                                <span className="font-bold text-textPrimary">01/11/2023</span>
                            </div>
                            <div className="flex justify-between items-center">
                                <span className="text-textSecondary">אמצעי תשלום:</span>
                                <div className="flex items-center gap-2">
                                    <div className="bg-gray-100 px-2 py-1 rounded text-xs font-bold text-gray-600">VISA</div>
                                    <span className="font-mono text-sm">•••• 4242</span>
                                </div>
                            </div>
                        </div>
                    )}

                    <div className="flex gap-4 mt-6">
                        <button 
                            onClick={() => push('/pricing')}
                            className="text-primary font-bold hover:bg-blue-50 px-4 py-2 rounded-lg transition-colors"
                        >
                            שדרוג תוכנית
                        </button>
                        {/* Cancel button - Only shown for paid users */}
                        {user?.plan !== 'Free' && (
                            <button className="text-red-600 font-medium hover:bg-red-50 px-4 py-2 rounded-lg transition-colors ml-auto">
                                ביטול מנוי
                            </button>
                        )}
                    </div>
                </Card>

                {/* Usage Stats */}
                <div className="space-y-6">
                    <Card className="p-6">
                        <h3 className="font-bold text-gray-900 mb-4">שימוש החודש</h3>
                        <div className="space-y-4">
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span>חיפושים</span>
                                    <span className="font-bold">145 / 500</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                    <div className="bg-primary h-2 rounded-full" style={{ width: '29%' }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span>פריטים במעקב</span>
                                    <span className="font-bold">12 / 50</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                    <div className="bg-green-500 h-2 rounded-full" style={{ width: '24%' }}></div>
                                </div>
                            </div>
                            <div>
                                <div className="flex justify-between text-sm mb-1">
                                    <span>התראות שנשלחו</span>
                                    <span className="font-bold">8</span>
                                </div>
                                <div className="w-full bg-gray-100 rounded-full h-2">
                                    <div className="bg-orange-400 h-2 rounded-full" style={{ width: '10%' }}></div>
                                </div>
                            </div>
                        </div>
                    </Card>

                    <Card className="p-6 bg-gray-50 border-dashed">
                        <h3 className="font-bold text-gray-700 mb-2">זקוקים לעזרה?</h3>
                        <p className="text-sm text-textSecondary mb-4">
                            צוות התמיכה שלנו זמין עבורך לכל שאלה הקשורה למנוי או לשימוש במערכת.
                        </p>
                        <button className="text-sm font-bold text-textPrimary border border-gray-300 bg-white px-4 py-2 rounded-lg hover:bg-gray-50 w-full">
                            פנייה לתמיכה
                        </button>
                    </Card>
                </div>
            </div>
        </PageLayout>
        </ProtectedRoute>
    );
}
