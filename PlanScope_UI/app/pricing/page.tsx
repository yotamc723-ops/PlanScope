'use client';

import React, { useState } from 'react';
import { useRouter } from '../../utils/nextShim';
import { Navbar, useAuth } from '../../components/Shared';

const WaitlistModal = ({ onClose }: { onClose: () => void }) => {
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        // Simulate API call
        setTimeout(() => {
            setLoading(false);
            setSubmitted(true);
        }, 1000);
    };

    if (submitted) {
        return (
            <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
                <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl text-center relative">
                    <button 
                        onClick={onClose} 
                        className="absolute top-4 left-4 text-gray-400 hover:text-gray-600 transition-colors p-1 hover:bg-gray-100 rounded-full"
                        title="סגור"
                    >
                        <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                    </button>
                    <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce-short">
                        <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                    </div>
                    <h3 className="text-xl font-bold text-gray-900 mb-2">תודה שנרשמת!</h3>
                    <p className="text-gray-600 mb-6">פרטייך התקבלו במערכת. ניצור איתך קשר בהקדם ברגע שהשירות העסקי יהיה זמין.</p>
                    <button onClick={onClose} className="bg-primary text-white px-6 py-2.5 rounded-lg font-bold hover:bg-primaryHover transition-colors w-full">
                        סגור
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-fade-in">
            <div className="bg-white rounded-2xl p-8 max-w-md w-full shadow-2xl relative">
                <button 
                    onClick={onClose} 
                    className="absolute top-4 left-4 text-gray-400 hover:text-gray-600 transition-colors p-1 hover:bg-gray-100 rounded-full"
                    title="סגור (יציאה ללא הרשמה)"
                >
                    <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
                
                <h3 className="text-2xl font-bold text-gray-900 mb-2">הצטרפות לרשימת המתנה</h3>
                <p className="text-gray-600 mb-6 text-sm">השאירו פרטים וניצור איתכם קשר כשהתוכנית העסקית (Enterprise) תהיה זמינה.</p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">שם פרטי</label>
                            <input required type="text" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all" placeholder="ישראל" />
                        </div>
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-1">שם משפחה</label>
                            <input required type="text" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all" placeholder="ישראלי" />
                        </div>
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">כתובת אימייל</label>
                        <input required type="email" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all" placeholder="name@company.com" />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-700 mb-1">שם החברה (אופציונלי)</label>
                        <input type="text" className="w-full px-3 py-2.5 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all" placeholder="שם החברה בע״מ" />
                    </div>

                    <button 
                        type="submit" 
                        disabled={loading}
                        className="w-full bg-slate-900 text-white py-3 rounded-lg font-bold hover:bg-slate-800 transition-all shadow-md mt-4 flex justify-center items-center gap-2"
                    >
                        {loading ? 'שולח...' : 'הרשמה לרשימה'}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default function PricingPage() {
    const { push } = useRouter();
    const { user } = useAuth();
    const [showWaitlist, setShowWaitlist] = useState(false);

    const handleUpgrade = () => {
        if (user) {
            push('/payment');
        } else {
            push('/login');
        }
    };

    return (
        <div className="min-h-screen bg-background font-sans">
            <Navbar />
            {showWaitlist && <WaitlistModal onClose={() => setShowWaitlist(false)} />}
            
            <div className="max-w-5xl mx-auto py-16 px-4">
                <div className="text-center mb-16 space-y-4 animate-fade-in">
                    <h1 className="text-4xl font-bold text-textPrimary">תוכניות ומחירים</h1>
                    <p className="text-xl text-textSecondary max-w-2xl mx-auto">
                        בחרו את המסלול המתאים ביותר לצרכים שלכם. אפשר לשדרג או לבטל בכל עת.
                    </p>
                </div>

                <div className="grid md:grid-cols-2 gap-8 max-w-4xl mx-auto items-stretch">
                    {/* Pro Plan - Existing */}
                    <div className="bg-white p-8 rounded-2xl border-2 border-primary relative shadow-2xl transform md:scale-105 z-10 flex flex-col order-1 md:order-none">
                        <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-primary text-white px-4 py-1 rounded-full text-sm font-bold shadow-sm tracking-wide">
                            הכי מומלץ
                        </div>
                        <h3 className="text-xl font-bold text-primary mb-2">Pro מקצועי</h3>
                        <div className="text-4xl font-black text-textPrimary mb-6 flex items-baseline gap-1">
                            39 ₪ <span className="text-lg font-normal text-textSecondary">/ חודש</span>
                        </div>
                        <p className="text-sm text-textSecondary mb-6 border-b border-border pb-4 w-full">
                            למקצוענים שצריכים להישאר תמיד עם האצבע על הדופק.
                        </p>
                        <ul className="space-y-4 mb-8 flex-grow w-full">
                            <li className="flex items-center gap-3 text-textPrimary font-medium">
                                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                    <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                </div>
                                <span>גישה מלאה לכל ארכיון המערכת</span>
                            </li>
                            <li className="flex items-center gap-3 text-textPrimary font-medium">
                                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                    <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                </div>
                                <span>מערכת סינון וחיפוש מתקדמת</span>
                            </li>
                            <li className="flex items-center gap-3 text-textPrimary font-medium">
                                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                    <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                </div>
                                <span>התראות במייל על אזורים נבחרים</span>
                            </li>
                            <li className="flex items-center gap-3 text-textPrimary font-medium">
                                <div className="w-5 h-5 rounded-full bg-blue-100 flex items-center justify-center flex-shrink-0">
                                    <svg className="w-3.5 h-3.5 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" /></svg>
                                </div>
                                <span>תמיכה טכנית בעדיפות גבוהה</span>
                            </li>
                        </ul>
                        <button onClick={handleUpgrade} className="w-full py-3.5 rounded-lg font-bold bg-primary text-white hover:bg-primaryHover transition-all shadow-md hover:shadow-lg">
                            שדרג ל-Pro עכשיו
                        </button>
                    </div>

                    {/* Enterprise Plan - New */}
                    <div className="bg-white p-8 rounded-2xl border border-border flex flex-col items-start hover:border-gray-300 transition-colors shadow-sm relative overflow-hidden order-2 md:order-none">
                        <div className="absolute top-4 left-4 bg-gray-900 text-white px-3 py-1 rounded-full text-xs font-bold tracking-wide shadow-sm">
                            בקרוב
                        </div>
                        <h3 className="text-xl font-bold text-textPrimary mb-2 mt-2">Enterprise עסקי</h3>
                        <div className="text-4xl font-black text-textPrimary mb-6 flex items-baseline gap-1 opacity-70">
                            200 ₪ <span className="text-lg font-normal text-textSecondary">/ חודש</span>
                        </div>
                        <p className="text-sm text-textSecondary mb-6 border-b border-border pb-4 w-full">
                            לעסקים שצריכים שליטה רחבה יותר.
                        </p>
                        <ul className="space-y-4 mb-8 flex-grow w-full">
                            <li className="flex items-center gap-3 text-textPrimary">
                                <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                <span>כל היתרונות של מנוי Pro</span>
                            </li>
                            <li className="flex items-center gap-3 text-textPrimary font-bold bg-blue-50 p-2 rounded-lg -mr-2">
                                <svg className="w-5 h-5 text-primary flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                <span>חיבור ומעקב ל-3 ערים במקביל</span>
                            </li>
                             <li className="flex items-center gap-3 text-textPrimary">
                                <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                <span>דוחות חודשיים מרוכזים</span>
                            </li>
                            <li className="flex items-center gap-3 text-textPrimary">
                                <svg className="w-5 h-5 text-green-500 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                <span>מנהל תיק לקוח אישי</span>
                            </li>
                        </ul>
                        <button onClick={() => setShowWaitlist(true)} className="w-full py-3 rounded-lg font-bold border border-slate-900 bg-slate-900 text-white hover:bg-slate-800 transition-all shadow-md">
                            הצטרפו לרשימת המתנה
                        </button>
                    </div>
                </div>

                <div className="text-center mt-12">
                    <p className="text-textSecondary text-sm">
                        * המחירים כוללים מע"מ. ניתן לבטל בכל עת ללא התחייבות.
                    </p>
                </div>
            </div>
        </div>
    );
}