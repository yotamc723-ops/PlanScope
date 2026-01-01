'use client';

import React, { useState } from 'react';
import { useRouter } from '../utils/nextShim';
import { Navbar, Chip } from '../components/Shared';

export default function LandingPage() {
  const { push } = useRouter();

  return (
    <div className="min-h-screen bg-background font-sans overflow-x-hidden">
        <Navbar />
        
        {/* Hero Section */}
        <section className="relative pt-20 pb-24 px-4 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-b from-blue-50/80 to-white -z-10"></div>
            <div className="absolute top-0 right-0 w-[500px] h-[500px] bg-primary/5 rounded-full blur-3xl -z-10 translate-x-1/3 -translate-y-1/4"></div>
            
            <div className="max-w-6xl mx-auto grid lg:grid-cols-2 gap-12 items-center">
                <div className="text-right space-y-8 animate-fade-in">
                    <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-blue-100/50 border border-blue-200 text-primary text-sm font-semibold">
                        <span className="relative flex h-2 w-2">
                          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
                          <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
                        </span>
                        מחובר כעת
                    </div>
                    
                    <h1 className="text-5xl md:text-7xl font-black text-slate-900 tracking-tight leading-[1.1]">
                        המודיעין התכנוני <br/>
                        <span className="text-transparent bg-clip-text bg-gradient-to-l from-primary to-blue-600">שמקדים את השוק</span>
                    </h1>
                    
                    <p className="text-xl text-slate-600 max-w-xl leading-relaxed">
                        אל תחכו לפרוטוקולים. קבלו התראות בזמן אמת על היתרים, תב"עות, בקשות והחלטות ועדה ישירות לנייד.
                        הכלי האולטימטיבי למתווכים, משקיעים ויזמים.
                    </p>
                    
                    <div className="flex flex-col sm:flex-row gap-4 pt-2">
                        <button onClick={() => push('/pricing')} className="bg-primary hover:bg-primaryHover text-white px-8 py-4 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-primary/30 flex items-center justify-center gap-2">
                            תכניות והרשמה
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-5 h-5 rotate-180">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                            </svg>
                        </button>
                        <button onClick={() => push('/demo/dashboard')} className="bg-white hover:bg-gray-50 text-slate-700 border border-border px-8 py-4 rounded-xl font-bold text-lg transition-all flex items-center justify-center gap-2 group">
                            <span className="group-hover:text-primary transition-colors">דמו חי</span>
                            <span className="bg-red-100 text-red-600 text-xs px-2 py-0.5 rounded-full font-bold">בת ים</span>
                        </button>
                    </div>
                    
                    <p className="text-sm text-slate-400">
                        * ללא צורך בכרטיס אשראי להרשמה • ביטול בכל עת
                    </p>
                </div>

                {/* Hero Visual - Abstract Dashboard Interface */}
                <div className="relative hidden lg:block">
                    <div className="absolute inset-0 bg-gradient-to-tr from-primary/20 to-transparent blur-2xl rounded-full"></div>
                    <div className="relative bg-white/60 backdrop-blur-xl border border-white/40 shadow-2xl rounded-2xl p-6 transform rotate-[-2deg] hover:rotate-0 transition-transform duration-700">
                        {/* Mock Card 1 */}
                        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 mb-4">
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex gap-2">
                                    <span className="bg-orange-100 text-orange-700 px-2 py-0.5 rounded text-xs font-bold">היתר בניה</span>
                                    <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">תל אביב</span>
                                </div>
                                <span className="text-xs text-gray-400">לפני 2 דקות</span>
                            </div>
                            <h3 className="font-bold text-gray-900 mb-1">הריסה והקמת בניין מגורים בן 8 קומות</h3>
                            <div className="text-sm text-gray-500 mb-3">רחוב דיזנגוף 100, תל אביב • גוש 6904 חלקה 12</div>
                            <div className="flex gap-2">
                                <div className="h-2 w-16 bg-gray-100 rounded-full overflow-hidden">
                                    <div className="h-full bg-green-500 w-3/4"></div>
                                </div>
                                <span className="text-xs text-gray-400">סטטוס: התקבל היתר</span>
                            </div>
                        </div>

                        {/* Mock Card 2 */}
                        <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-4 opacity-90 scale-95 origin-bottom">
                            <div className="flex justify-between items-start mb-3">
                                <div className="flex gap-2">
                                    <span className="bg-blue-100 text-blue-700 px-2 py-0.5 rounded text-xs font-bold">ישיבת ועדה</span>
                                    <span className="bg-gray-100 text-gray-600 px-2 py-0.5 rounded text-xs">רמת גן</span>
                                </div>
                                <span className="text-xs text-gray-400">עכשיו</span>
                            </div>
                            <h3 className="font-bold text-gray-900 mb-1">אישור תכנית פינוי בינוי מתחם נגבה</h3>
                            <div className="text-sm text-gray-500">נוסף פרוטוקול חדש עם 12 החלטות...</div>
                        </div>
                        
                        {/* Notification Badge */}
                        <div className="absolute -top-4 -right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg font-bold text-sm animate-bounce">
                            🔔 3 התראות חדשות
                        </div>
                    </div>
                </div>
            </div>
        </section>

        {/* Real Value Stats */}
        <section className="bg-white border-y border-border py-10">
            <div className="max-w-6xl mx-auto px-4 grid grid-cols-2 md:grid-cols-3 gap-8 divide-x divide-x-reverse divide-gray-100">
                <div className="text-center relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-blue-600 text-white text-[10px] font-bold px-2 py-0.5 rounded-full shadow-sm rotate-2 whitespace-nowrap z-10">
                        עוד בקרוב!
                    </div>
                    <div className="text-3xl font-black text-slate-900 mb-1">1</div>
                    <div className="text-sm text-slate-500 font-medium">עיריות במעקב</div>
                </div>
                <div className="text-center">
                    <div className="text-3xl font-black text-slate-900 mb-1">24/7</div>
                    <div className="text-sm text-slate-500 font-medium">ניטור רציף של ועדות</div>
                </div>
                <div className="text-center">
                    <div className="text-3xl font-black text-slate-900 mb-1">0</div>
                    <div className="text-sm text-slate-500 font-medium">פספוסים של הזדמנויות</div>
                </div>
            </div>
        </section>

        {/* Comparison Section */}
        <section className="py-24 px-4 bg-slate-50">
            <div className="max-w-4xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold text-slate-900">הדרך הישנה מול הדרך החדשה</h2>
                    <p className="text-slate-500 mt-2">למה להמשיך לחפש ידנית כשהטכנולוגיה יכולה לעבוד בשבילך?</p>
                </div>

                <div className="grid md:grid-cols-2 gap-8">
                    {/* The Old Way */}
                    <div className="bg-white p-8 rounded-2xl border border-red-100 shadow-sm opacity-70">
                        <h3 className="text-xl font-bold text-slate-700 mb-6 flex items-center gap-2">
                            <span className="text-2xl">😫</span> העבודה הידנית
                        </h3>
                        <ul className="space-y-4">
                            <li className="flex items-start gap-3 text-slate-600">
                                <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                כניסה יומית לעשרות אתרי עיריות שונים
                            </li>
                            <li className="flex items-start gap-3 text-slate-600">
                                <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                קבצי PDF סרוקים שלא ניתן לחפש בהם
                            </li>
                            <li className="flex items-start gap-3 text-slate-600">
                                <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                גילוי מאוחר מדי על התנגדויות או הזדמנויות
                            </li>
                            <li className="flex items-start gap-3 text-slate-600">
                                <svg className="w-5 h-5 text-red-400 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                                ניהול מעקב בטבלאות אקסל מסורבלות
                            </li>
                        </ul>
                    </div>

                    {/* The New Way */}
                    <div className="bg-white p-8 rounded-2xl border-2 border-primary shadow-xl relative overflow-hidden">
                        <div className="absolute top-0 right-0 bg-primary text-white text-xs font-bold px-3 py-1 rounded-bl-lg">הבחירה החכמה</div>
                        <h3 className="text-xl font-bold text-primary mb-6 flex items-center gap-2">
                            <span className="text-2xl">🚀</span> Municipal Dashboard
                        </h3>
                        <ul className="space-y-4">
                            <li className="flex items-start gap-3 text-slate-800 font-medium">
                                <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                מרכז שליטה אחד לכל הרשויות בארץ
                            </li>
                            <li className="flex items-start gap-3 text-slate-800 font-medium">
                                <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                חיפוש חכם בתוך תוכן המסמכים (OCR)
                            </li>
                            <li className="flex items-start gap-3 text-slate-800 font-medium">
                                <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                התראות "פוש" ומייל בזמן אמת על שינויים בגוש/חלקה
                            </li>
                            <li className="flex items-start gap-3 text-slate-800 font-medium">
                                <svg className="w-5 h-5 text-green-500 mt-0.5 shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                                "רשימת מעקב" אוטומטית לניהול פרויקטים
                            </li>
                        </ul>
                    </div>
                </div>
            </div>
        </section>

        {/* Persona Section */}
        <section className="py-24 px-4 bg-white">
            <div className="max-w-6xl mx-auto">
                <div className="text-center mb-16">
                    <h2 className="text-3xl font-bold text-slate-900">מותאם בדיוק לצרכים שלך</h2>
                </div>
                <div className="grid md:grid-cols-3 gap-8">
                    <div className="group p-8 rounded-2xl bg-gray-50 hover:bg-white hover:shadow-xl border border-gray-100 transition-all duration-300">
                        <div className="w-14 h-14 bg-blue-100 text-blue-600 rounded-2xl flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">🤝</div>
                        <h3 className="text-xl font-bold text-slate-900 mb-3">מתווכי נדל"ן</h3>
                        <p className="text-slate-600 leading-relaxed">
                            השיגו בלעדיות על המידע. אתרו נכסים במוקדיי התחדשות עירונית לפני שהם יוצאים לשוק, והרשימו לקוחות עם בקיאות תכנונית מלאה.
                        </p>
                    </div>
                    <div className="group p-8 rounded-2xl bg-gray-50 hover:bg-white hover:shadow-xl border border-gray-100 transition-all duration-300">
                        <div className="w-14 h-14 bg-purple-100 text-purple-600 rounded-2xl flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">📊</div>
                        <h3 className="text-xl font-bold text-slate-900 mb-3">משקיעים</h3>
                        <p className="text-slate-600 leading-relaxed">
                            זהו את הפוטנציאל לפני כולם. נתחו מגמות, שינויי ייעוד והזדמנויות השבחה. קבלו החלטות מבוססות דאטה ולא שמועות.
                        </p>
                    </div>
                    <div className="group p-8 rounded-2xl bg-gray-50 hover:bg-white hover:shadow-xl border border-gray-100 transition-all duration-300">
                        <div className="w-14 h-14 bg-orange-100 text-orange-600 rounded-2xl flex items-center justify-center text-3xl mb-6 group-hover:scale-110 transition-transform">🏗️</div>
                        <h3 className="text-xl font-bold text-slate-900 mb-3">יזמים</h3>
                        <p className="text-slate-600 leading-relaxed">
                            אתרו הזדמנויות תמ"א 38 ופינוי בינוי לפני המתחרים. קבלו מידע על הפקדות תב"ע ושינויי מדיניות ברגע שהם קורים.
                        </p>
                    </div>
                </div>
            </div>
        </section>
        
        {/* CTA Section */}
        <section className="py-20 px-4 bg-slate-900 text-white relative overflow-hidden">
            <div className="absolute top-0 left-0 w-full h-full bg-[url('https://www.transparenttextures.com/patterns/cubes.png')] opacity-10"></div>
            <div className="max-w-4xl mx-auto text-center relative z-10 space-y-8">
                <h2 className="text-3xl md:text-5xl font-black mb-4">אל תתנו למידע לחמוק מכם</h2>
                <p className="text-xl text-gray-300 max-w-2xl mx-auto">
                    הצטרפו למאות אנשי מקצוע שכבר משתמשים ב-Municipal Dashboard כדי לקבל החלטות חכמות יותר, מהר יותר.
                </p>
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                    <button onClick={() => push('/pricing')} className="bg-primary hover:bg-primaryHover text-white px-10 py-4 rounded-xl font-bold text-lg transition-all shadow-lg hover:shadow-primary/50 transform hover:-translate-y-1">
                        תכניות והרשמה
                    </button>
                    <button onClick={() => push('/login')} className="bg-transparent border-2 border-white/20 hover:bg-white/10 text-white px-10 py-4 rounded-xl font-bold text-lg transition-all">
                        כניסה למנויים
                    </button>
                </div>
            </div>
        </section>

        {/* Footer */}
        <footer className="bg-slate-950 text-slate-400 py-12 px-4 border-t border-slate-800">
            <div className="max-w-6xl mx-auto grid md:grid-cols-4 gap-8">
                <div className="col-span-1 md:col-span-2">
                    <div className="flex items-center gap-2 mb-4">
                        <div className="bg-primary text-white p-1 rounded">
                            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z" />
                            </svg>
                        </div>
                        <span className="font-bold text-white text-lg">Municipal Dashboard</span>
                    </div>
                    <p className="text-sm max-w-sm mb-6">
                        המערכת המובילה בישראל לניטור וניתוח מידע תכנוני מוניציפלי. אנחנו הופכים מידע גולמי לתובנות עסקיות.
                    </p>
                </div>
                <div>
                    <h4 className="font-bold text-white mb-4">מוצר</h4>
                    <ul className="space-y-2 text-sm">
                        <li><a href="#" className="hover:text-primary transition-colors">אודות</a></li>
                        <li><a href="/pricing" className="hover:text-primary transition-colors">מחירים</a></li>
                        <li><a href="/dashboard" className="hover:text-primary transition-colors">דמו מערכת</a></li>
                        <li><a href="#" className="hover:text-primary transition-colors">API למפתחים</a></li>
                    </ul>
                </div>
                <div>
                    <h4 className="font-bold text-white mb-4">תמיכה</h4>
                    <ul className="space-y-2 text-sm">
                        <li><a href="#" className="hover:text-primary transition-colors">מרכז עזרה</a></li>
                        <li><a href="#" className="hover:text-primary transition-colors">צור קשר</a></li>
                        <li><a href="#" className="hover:text-primary transition-colors">תנאי שימוש</a></li>
                        <li><a href="#" className="hover:text-primary transition-colors">מדיניות פרטיות</a></li>
                    </ul>
                </div>
            </div>
            <div className="max-w-6xl mx-auto mt-12 pt-8 border-t border-slate-800 text-center text-xs">
                © {new Date().getFullYear()} Municipal Dashboard. כל הזכויות שמורות.
            </div>
        </footer>
    </div>
  );
}