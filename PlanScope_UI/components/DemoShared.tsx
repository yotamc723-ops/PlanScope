import React from 'react';
import { PageLayout } from './Shared';

export const DemoBanner = () => (
    <div className="fixed bottom-6 left-6 z-[60] flex items-center gap-2 bg-red-600 text-white px-4 py-2 rounded-full shadow-lg border-2 border-white/20 animate-bounce-slow">
        <span className="text-xl">⚠️</span>
        <div className="flex flex-col">
            <span className="text-xs font-bold uppercase tracking-wider">מצב דמו</span>
            <span className="text-[10px] opacity-90">נתונים להמחשה בלבד (בת ים)</span>
        </div>
    </div>
);

export const DemoLayout = ({ children, backLink }: { children?: React.ReactNode, backLink?: string }) => {
    return (
        <div className="relative">
            <div className="bg-stripes fixed inset-0 pointer-events-none z-0 opacity-[0.03]"></div>
            <PageLayout backLink={backLink}>
                {children}
            </PageLayout>
            <DemoBanner />
            <style jsx global>{`
                .bg-stripes {
                    background-image: repeating-linear-gradient(
                        45deg,
                        #000,
                        #000 10px,
                        transparent 10px,
                        transparent 20px
                    );
                }
                @keyframes bounce-slow {
                    0%, 100% { transform: translateY(0); }
                    50% { transform: translateY(-5px); }
                }
                .animate-bounce-slow {
                    animation: bounce-slow 3s infinite;
                }
            `}</style>
        </div>
    );
};