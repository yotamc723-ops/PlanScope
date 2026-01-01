import React, { useEffect } from 'react';
import { useRouter } from '../utils/nextShim';
import { useAuth } from './Shared';

interface PaidRouteProps {
  children: React.ReactNode;
}

/**
 * PaidRoute - Wrapper component for pages that require a paid subscription
 * 
 * If the user is not authenticated, they will be redirected to /login
 * If the user has a Free plan, they will be redirected to /pricing
 * If authentication is still loading, a loading spinner is shown
 */
export const PaidRoute = ({ children }: PaidRouteProps) => {
  const { user, loading } = useAuth();
  const { push } = useRouter();

  useEffect(() => {
    // Only redirect after loading is complete
    if (!loading) {
      if (!user) {
        push('/login');
      } else if (user.plan === 'Free') {
        push('/pricing');
      }
    }
  }, [user, loading, push]);

  // Show loading spinner while checking auth state
  if (loading) {
    return (
      <div className="min-h-screen bg-background flex items-center justify-center">
        <div className="text-center">
          <div className="w-12 h-12 border-4 border-gray-200 border-t-primary rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-textSecondary">טוען...</p>
        </div>
      </div>
    );
  }

  // Don't render children if not authenticated or free user
  if (!user || user.plan === 'Free') {
    return null;
  }

  // User is authenticated with paid plan, render the content
  return <>{children}</>;
};

export default PaidRoute;

