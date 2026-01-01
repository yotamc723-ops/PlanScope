import React from 'react';
import { createRoot } from 'react-dom/client';
import RootLayout from './app/layout';
import LandingPage from './app/page';
import DashboardPage from './app/dashboard/page';
import PricingPage from './app/pricing/page';
import WatchlistPage from './app/watchlist/page';
import LoginPage from './app/login/page';
import MyPlanPage from './app/my-plan/page';
import PaymentPage from './app/payment/page';
import MeetingDetailPage from './app/dashboard/meetings/[id]/page';
import PermitDetailPage from './app/dashboard/permits/[id]/page';
import ApplicationDetailPage from './app/dashboard/applications/[id]/page';
import PlanDetailPage from './app/dashboard/plans/[id]/page';
// Demo Pages
import DemoDashboardPage from './app/demo/dashboard/page';
import DemoMeetingDetailPage from './app/demo/meetings/[id]/page';
import DemoPermitDetailPage from './app/demo/permits/[id]/page';
import DemoApplicationDetailPage from './app/demo/applications/[id]/page';
import DemoPlanDetailPage from './app/demo/plans/[id]/page';

import { NextRouterProvider, usePathname, matchRoute } from './utils/nextShim';
import { AuthProvider } from './components/Shared';

// Simple Router Component
const AppRouter = () => {
    const path = usePathname();

    // Static Routes
    if (path === '/' || path === '/home') {
        return <LandingPage />;
    }
    
    if (path === '/pricing') {
        return <PricingPage />;
    }

    if (path === '/login') {
        return <LoginPage />;
    }

    if (path === '/payment') {
        return <PaymentPage />;
    }

    if (path === '/dashboard') {
        return <DashboardPage />;
    }
    
    if (path === '/watchlist') {
        return <WatchlistPage />;
    }
    
    if (path === '/my-plan') {
        return <MyPlanPage />;
    }
    
    // Demo Routes
    if (path === '/demo/dashboard') {
        return <DemoDashboardPage />;
    }
    if (matchRoute('/demo/meetings/[id]', path)) {
        return <DemoMeetingDetailPage />;
    }
    if (matchRoute('/demo/permits/[id]', path)) {
        return <DemoPermitDetailPage />;
    }
    if (matchRoute('/demo/applications/[id]', path)) {
        return <DemoApplicationDetailPage />;
    }
    if (matchRoute('/demo/plans/[id]', path)) {
        return <DemoPlanDetailPage />;
    }
    
    // Check dynamic routes
    if (matchRoute('/dashboard/meetings/[id]', path)) {
        return <MeetingDetailPage />;
    }
    
    if (matchRoute('/dashboard/permits/[id]', path)) {
        return <PermitDetailPage />;
    }

    if (matchRoute('/dashboard/applications/[id]', path)) {
        return <ApplicationDetailPage />;
    }

    if (matchRoute('/dashboard/plans/[id]', path)) {
        return <PlanDetailPage />;
    }

    // Default 404 behavior or fallback to landing
    return <LandingPage />;
};

const root = createRoot(document.getElementById('root') as HTMLElement);
root.render(
  <React.StrictMode>
    <NextRouterProvider>
      <AuthProvider>
        <RootLayout>
            <AppRouter />
        </RootLayout>
      </AuthProvider>
    </NextRouterProvider>
  </React.StrictMode>
);