import React, { useEffect } from 'react';
import { useRouter } from '../utils/nextShim';
import { useAuth } from './Shared';

interface ProtectedRouteProps {
  children: React.ReactNode;
}

/**
 * ProtectedRoute - Wrapper component for pages that require authentication
 * 
 * If the user is not authenticated, they will be redirected to /login
 * If authentication is still loading, a loading spinner is shown
 */
export const ProtectedRoute = ({ children }: ProtectedRouteProps) => {
  const { user, loading } = useAuth();
  const { push } = useRouter();

  useEffect(() => {
    // Only redirect after loading is complete and there's no user
    if (!loading && !user) {
      push('/login');
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

  // Don't render children if not authenticated
  if (!user) {
    return null;
  }

  // User is authenticated, render the protected content
  return <>{children}</>;
};

export default ProtectedRoute;

