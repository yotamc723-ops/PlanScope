'use client';

import React, { useState } from 'react';
import { useRouter } from '../../utils/nextShim';
import { PageLayout, Card, LoadingState } from '../../components/Shared';
import { ProtectedRoute } from '../../components/ProtectedRoute';

export default function PaymentPage() {
    const { push } = useRouter();
    const [processing, setProcessing] = useState(false);
    const [success, setSuccess] = useState(false);

    const handlePayment = (e: React.FormEvent) => {
        e.preventDefault();
        setProcessing(true);
        
        // Simulate API call
        setTimeout(() => {
            setProcessing(false);
            setSuccess(true);
            
            // Redirect after success
            setTimeout(() => {
                push('/my-plan');
            }, 2000);
        }, 2000);
    };

    if (success) {
        return (
            <ProtectedRoute>
            <PageLayout>
                <div className="flex flex-col items-center justify-center py-20 animate-fade-in">
                    <div className="w-20 h-20 bg-green-100 rounded-full flex items-center justify-center mb-6">
                        <svg className="w-10 h-10 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
                        </svg>
                    </div>
                    <h1 className="text-3xl font-bold text-textPrimary mb-2">התשלום עבר בהצלחה!</h1>
                    <p className="text-textSecondary mb-8">המנוי שלך שודרג בהצלחה. אתה מועבר לאזור האישי...</p>
                </div>
            </PageLayout>
            </ProtectedRoute>
        );
    }

    return (
        <ProtectedRoute>
        <PageLayout backLink="/pricing">
            <div className="max-w-4xl mx-auto grid md:grid-cols-3 gap-8 items-start">
                
                {/* Order Summary */}
                <div className="md:col-span-1 space-y-6">
                    <h2 className="text-xl font-bold text-textPrimary">סיכום הזמנה</h2>
                    <Card className="p-6 bg-gray-50 border-gray-200">
                        <div className="flex justify-between items-start mb-4 border-b border-gray-200 pb-4">
                            <div>
                                <h3 className="font-bold text-lg">מנוי Pro</h3>
                                <p className="text-sm text-textSecondary">חיוב חודשי</p>
                            </div>
                            <span className="font-bold text-lg">39 ₪</span>
                        </div>
                        <div className="space-y-2 text-sm text-textSecondary mb-6">
                            <div className="flex justify-between">
                                <span>סכום ביניים</span>
                                <span>33.33 ₪</span>
                            </div>
                            <div className="flex justify-between">
                                <span>מע"מ (17%)</span>
                                <span>5.67 ₪</span>
                            </div>
                        </div>
                        <div className="flex justify-between items-center font-black text-xl text-textPrimary pt-4 border-t border-gray-200">
                            <span>סה"כ לתשלום</span>
                            <span>39 ₪</span>
                        </div>
                    </Card>
                    
                    <div className="flex items-center justify-center gap-2 text-gray-400 text-sm">
                        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" /></svg>
                        תשלום מאובטח בתקן SSL
                    </div>
                </div>

                {/* Payment Form */}
                <div className="md:col-span-2">
                    <h2 className="text-xl font-bold text-textPrimary mb-6">פרטי תשלום</h2>
                    <Card className="p-8">
                        <form onSubmit={handlePayment} className="space-y-6">
                            <div>
                                <label className="block text-sm font-medium text-textSecondary mb-2">שם על הכרטיס</label>
                                <input 
                                    required
                                    type="text" 
                                    className="w-full px-4 py-3 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                                    placeholder="ישראל ישראלי"
                                />
                            </div>

                            <div>
                                <label className="block text-sm font-medium text-textSecondary mb-2">מספר כרטיס אשראי</label>
                                <div className="relative">
                                    <input 
                                        required
                                        dir="ltr"
                                        type="text" 
                                        maxLength={19}
                                        className="w-full pl-12 pr-4 py-3 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-mono text-left"
                                        placeholder="0000 0000 0000 0000"
                                    />
                                    <svg className="absolute left-4 top-3.5 w-5 h-5 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                                    </svg>
                                </div>
                            </div>

                            <div className="grid grid-cols-2 gap-6">
                                <div>
                                    <label className="block text-sm font-medium text-textSecondary mb-2">תוקף</label>
                                    <input 
                                        required
                                        dir="ltr"
                                        type="text" 
                                        maxLength={5}
                                        className="w-full px-4 py-3 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-mono text-center"
                                        placeholder="MM/YY"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-textSecondary mb-2">CVV</label>
                                    <input 
                                        required
                                        dir="ltr"
                                        type="text" 
                                        maxLength={3}
                                        className="w-full px-4 py-3 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all font-mono text-center"
                                        placeholder="123"
                                    />
                                </div>
                            </div>

                            <div className="pt-4">
                                <button 
                                    type="submit" 
                                    disabled={processing}
                                    className="w-full bg-primary hover:bg-primaryHover text-white py-4 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-primary/30 flex items-center justify-center gap-3 disabled:opacity-70 disabled:cursor-not-allowed"
                                >
                                    {processing ? (
                                        <>
                                            <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                            מעבד תשלום...
                                        </>
                                    ) : (
                                        <>
                                            בצע תשלום
                                        </>
                                    )}
                                </button>
                            </div>
                        </form>
                    </Card>
                </div>
            </div>
        </PageLayout>
        </ProtectedRoute>
    );
}