import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

// Context to hold current route state
interface RouterContextType {
  path: string;
  push: (path: string) => void;
  params: Record<string, string>;
}

const RouterContext = createContext<RouterContextType>({
  path: '/',
  push: () => {},
  params: {}
});

// Helper to match paths like /dashboard/meetings/[id] against /dashboard/meetings/123
export const matchRoute = (pattern: string, path: string): Record<string, string> | null => {
  const patternParts = pattern.split('/').filter(Boolean);
  const pathParts = path.split('/').filter(Boolean);

  if (patternParts.length !== pathParts.length) return null;

  const params: Record<string, string> = {};
  for (let i = 0; i < patternParts.length; i++) {
    const patternPart = patternParts[i];
    const pathPart = pathParts[i];

    if (patternPart.startsWith('[') && patternPart.endsWith(']')) {
      const key = patternPart.slice(1, -1);
      params[key] = pathPart;
    } else if (patternPart !== pathPart) {
      return null;
    }
  }
  return params;
};

// Provider Component
export const NextRouterProvider = ({ children }: { children?: ReactNode }) => {
  // Default to "/" (Home/Landing) for the initial route
  const [path, setPath] = useState('/');

  useEffect(() => {
    // Attempt to sync with browser history if possible, but don't crash.
    const handlePopState = () => {
        try {
            setPath(window.location.pathname === '/' || window.location.pathname === '' ? '/' : window.location.pathname);
        } catch (e) {
            // ignore
        }
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const push = (newPath: string) => {
    try {
      // Try to update the URL bar, but catch errors if running in a sandbox/blob
      window.history.pushState({}, '', newPath);
    } catch (e) {
      console.warn('Routing fallback: Unable to pushState (likely due to sandbox environment). Using memory routing.', e);
    }
    // Always update internal state
    setPath(newPath);
  };

  const getParams = () => {
    // Hardcoded knowledge of app routes for the shim
    const routes = [
      '/dashboard/meetings/[id]',
      '/dashboard/permits/[id]',
      '/dashboard/applications/[id]',
      '/dashboard/plans/[id]',
      '/demo/meetings/[id]',
      '/demo/permits/[id]',
      '/demo/applications/[id]',
      '/demo/plans/[id]'
    ];
    for (const route of routes) {
      const p = matchRoute(route, path);
      if (p) return p;
    }
    return {};
  };

  return (
    <RouterContext.Provider value={{ path, push, params: getParams() }}>
      {children}
    </RouterContext.Provider>
  );
};

// --- Next.js Hooks Shim ---

export const useRouter = () => {
  const { push } = useContext(RouterContext);
  return { push };
};

export const useParams = () => {
  const { params } = useContext(RouterContext);
  return params;
};

export const usePathname = () => {
  const { path } = useContext(RouterContext);
  return path;
};

// --- Link Component Shim ---

export const Link = ({ href, children, className }: { href: string; children?: ReactNode; className?: string }) => {
  const { push } = useContext(RouterContext);
  
  const handleClick = (e: React.MouseEvent) => {
    e.preventDefault();
    push(href);
  };

  return (
    <a href={href} onClick={handleClick} className={className}>
      {children}
    </a>
  );
};

export default { useRouter, useParams, usePathname, Link };