'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from '../../utils/nextShim';
import { useAuth, Navbar } from '../../components/Shared';
import { isMagicLinkSignIn } from '../../config/firebase';

export default function LoginPage() {
    const { 
        user,
        loading, 
        signInWithGoogle, 
        sendMagicLink, 
        completeMagicLink,
        emailSent, 
        error 
    } = useAuth();
    const { push } = useRouter();
    const [email, setEmail] = useState('');
    const [isProcessingMagicLink, setIsProcessingMagicLink] = useState(false);

    // Redirect if already logged in
    useEffect(() => {
        if (user && !loading) {
            push('/dashboard');
        }
    }, [user, loading, push]);

    // Handle magic link on page load
    useEffect(() => {
        if (isMagicLinkSignIn()) {
            setIsProcessingMagicLink(true);
            completeMagicLink().finally(() => {
                setIsProcessingMagicLink(false);
            });
        }
    }, []);

    const handleMagicLinkSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (email.trim()) {
            await sendMagicLink(email.trim());
        }
    };

    // Show processing state when completing magic link sign-in
    if (isProcessingMagicLink) {
        return (
            <div className="min-h-screen bg-background font-sans flex flex-col">
                <Navbar />
                <div className="flex-grow flex items-center justify-center p-4">
                    <div className="bg-white p-8 rounded-2xl border border-border shadow-lg max-w-md w-full text-center">
                        <div className="w-16 h-16 border-4 border-gray-200 border-t-primary rounded-full animate-spin mx-auto mb-6"></div>
                        <h2 className="text-xl font-bold text-textPrimary mb-2">משלים את ההתחברות...</h2>
                        <p className="text-textSecondary">רגע אחד בבקשה</p>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-background font-sans flex flex-col">
            <Navbar />
            <div className="flex-grow flex items-center justify-center p-4">
                <div className="bg-white p-8 rounded-2xl border border-border shadow-lg max-w-md w-full animate-fade-in">
                    <div className="text-center mb-8">
                        <div className="inline-block bg-primary/10 p-3 rounded-full mb-4">
                            <svg className="w-8 h-8 text-primary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                            </svg>
                        </div>
                        <h1 className="text-2xl font-bold text-textPrimary">התחברות למערכת</h1>
                        <p className="text-textSecondary mt-2">גישה למידע תכנוני מתקדם</p>
                    </div>

                    {/* Error message */}
                    {error && (
                        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700 text-sm">
                            <div className="flex items-center gap-2">
                                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                <span>{error}</span>
                            </div>
                        </div>
                    )}

                    {/* Email sent success message */}
                    {emailSent ? (
                        <div className="text-center space-y-6">
                            <div className="bg-green-50 border border-green-200 rounded-xl p-6">
                                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg className="w-8 h-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                    </svg>
                                </div>
                                <h2 className="text-xl font-bold text-green-800 mb-2">בדוק את האימייל שלך!</h2>
                                <p className="text-green-700 text-sm">
                                    שלחנו לינק התחברות ל-<strong>{email}</strong>
                                </p>
                                <p className="text-green-600 text-xs mt-2">
                                    לחץ על הלינק באימייל כדי להתחבר
                                </p>
                            </div>
                            
                            <button 
                                onClick={() => window.location.reload()}
                                className="text-sm text-textSecondary hover:text-primary transition-colors"
                            >
                                לא קיבלת? לחץ כאן לשלוח שוב
                            </button>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {/* Google Sign In */}
                            <button 
                                onClick={signInWithGoogle}
                                disabled={loading}
                                className="w-full flex items-center justify-center gap-3 bg-white border border-border hover:bg-gray-50 text-textPrimary py-3 rounded-lg font-medium transition-all hover:shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                                {loading ? (
                                    <span className="w-5 h-5 border-2 border-gray-300 border-t-primary rounded-full animate-spin"></span>
                                ) : (
                                    <>
                                        <svg className="w-5 h-5" viewBox="0 0 24 24">
                                            <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                                            <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                                            <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.84z" fill="#FBBC05"/>
                                            <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                                        </svg>
                                        <span>המשך עם Google</span>
                                    </>
                                )}
                            </button>
                            
                            <div className="relative flex items-center py-2">
                                <div className="flex-grow border-t border-gray-200"></div>
                                <span className="flex-shrink-0 mx-4 text-gray-400 text-sm">או</span>
                                <div className="flex-grow border-t border-gray-200"></div>
                            </div>

                            {/* Magic Link Form */}
                            <form onSubmit={handleMagicLinkSubmit} className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-textSecondary mb-1">כתובת אימייל</label>
                                    <input 
                                        type="email" 
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="your@email.com" 
                                        required
                                        className="w-full px-4 py-2.5 rounded-lg border border-border focus:ring-2 focus:ring-primary/20 focus:border-primary outline-none transition-all"
                                    />
                                </div>
                                <button 
                                    type="submit" 
                                    disabled={loading || !email.trim()}
                                    className="w-full bg-primary hover:bg-primaryHover text-white py-3 rounded-lg font-bold transition-all shadow-md hover:shadow-lg disabled:opacity-70 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                                >
                                    {loading ? (
                                        <span className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></span>
                                    ) : (
                                        <>
                                            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                                            </svg>
                                            <span>שלח לינק התחברות</span>
                                        </>
                                    )}
                                </button>
                            </form>

                            <p className="text-xs text-center text-textSecondary mt-4">
                                נשלח לך לינק להתחברות ישירות למייל - ללא צורך בסיסמה
                            </p>
                        </div>
                    )}

                    <div className="mt-6 text-center text-sm text-textSecondary">
                        אין לך חשבון? <a href="/pricing" onClick={(e) => { e.preventDefault(); push('/pricing'); }} className="text-primary font-bold hover:underline">הירשם עכשיו</a>
                    </div>
                </div>
            </div>
        </div>
    );
}
