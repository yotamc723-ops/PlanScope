import React, { useState, useEffect, createContext, useContext } from 'react';
import { Link, usePathname, useRouter } from '../utils/nextShim';
import { User as FirebaseUser, onAuthStateChanged, signInWithPopup, signOut } from 'firebase/auth';
import { doc, getDoc, updateDoc, serverTimestamp } from 'firebase/firestore';
import { auth, db, googleProvider, sendMagicLinkEmail, isMagicLinkSignIn, completeMagicLinkSignIn } from '../config/firebase';

// --- Auth Context ---

// User type matching Firestore schema
interface User {
  uid: string;
  email: string;
  name: string;
  avatar?: string;
  plan: 'Free' | 'Pro' | 'Enterprise';
  subscriptionStatus: 'active' | 'canceled' | 'past_due' | 'trialing';
  emailNotifications: boolean;
  onboardingCompleted: boolean;
  preferredCity: string | null;
}

interface AuthContextType {
  user: User | null;
  firebaseUser: FirebaseUser | null;
  loading: boolean;
  signInWithGoogle: () => Promise<void>;
  sendMagicLink: (email: string) => Promise<void>;
  completeMagicLink: () => Promise<void>;
  logout: () => Promise<void>;
  emailSent: boolean;
  error: string | null;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  firebaseUser: null,
  loading: true,
  signInWithGoogle: async () => {},
  sendMagicLink: async () => {},
  completeMagicLink: async () => {},
  logout: async () => {},
  emailSent: false,
  error: null,
});

export const useAuth = () => useContext(AuthContext);

// Helper to convert Firestore user doc to User type
const mapFirestoreUserToUser = (data: any): User => {
  const planMap: Record<string, 'Free' | 'Pro' | 'Enterprise'> = {
    'free': 'Free',
    'pro': 'Pro',
    'enterprise': 'Enterprise',
  };
  
  return {
    uid: data.uid,
    email: data.email,
    name: data.displayName || data.email?.split('@')[0] || 'User',
    avatar: data.photoURL || `https://ui-avatars.com/api/?name=${encodeURIComponent(data.displayName || data.email || 'U')}&background=1a73e8&color=fff`,
    plan: planMap[data.subscriptionPlan] || 'Free',
    subscriptionStatus: data.subscriptionStatus || 'active',
    emailNotifications: data.emailNotifications ?? true,
    onboardingCompleted: data.onboardingCompleted ?? false,
    preferredCity: data.preferredCity || null,
  };
};

export const AuthProvider = ({ children }: { children?: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [firebaseUser, setFirebaseUser] = useState<FirebaseUser | null>(null);
  const [loading, setLoading] = useState(true);
  const [emailSent, setEmailSent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { push } = useRouter();

  // Fetch user document from Firestore
  const fetchUserDoc = async (uid: string): Promise<User | null> => {
    try {
      const userRef = doc(db, 'users', uid);
      const userSnap = await getDoc(userRef);
      
      if (userSnap.exists()) {
        return mapFirestoreUserToUser(userSnap.data());
      }
      return null;
    } catch (err) {
      console.error('Error fetching user document:', err);
      return null;
    }
  };

  // Update lastLoginAt in Firestore
  const updateLastLogin = async (uid: string) => {
    try {
      const userRef = doc(db, 'users', uid);
      await updateDoc(userRef, {
        lastLoginAt: serverTimestamp(),
      });
    } catch (err) {
      console.error('Error updating lastLoginAt:', err);
    }
  };

  // Listen for auth state changes
  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (fbUser) => {
      setFirebaseUser(fbUser);
      
      if (fbUser) {
        // User is signed in
        const userData = await fetchUserDoc(fbUser.uid);
        if (userData) {
          setUser(userData);
          await updateLastLogin(fbUser.uid);
        } else {
          // User document doesn't exist yet (might be creating)
          // Wait a moment for the Cloud Function to create it
          setTimeout(async () => {
            const retryUserData = await fetchUserDoc(fbUser.uid);
            if (retryUserData) {
              setUser(retryUserData);
            }
          }, 2000);
        }
      } else {
        // User is signed out
        setUser(null);
      }
      
      setLoading(false);
    });

    return () => unsubscribe();
  }, []);

  // Check for magic link on mount
  useEffect(() => {
    if (isMagicLinkSignIn()) {
      completeMagicLink();
    }
  }, []);

  // Sign in with Google
  const signInWithGoogle = async () => {
    setError(null);
    setLoading(true);
    try {
      await signInWithPopup(auth, googleProvider);
      push('/dashboard');
    } catch (err: any) {
      console.error('Google sign-in error:', err);
      setError(err.message || 'Failed to sign in with Google');
      setLoading(false);
    }
  };

  // Send magic link email
  const sendMagicLink = async (email: string) => {
    setError(null);
    setEmailSent(false);
    try {
      await sendMagicLinkEmail(email);
      setEmailSent(true);
    } catch (err: any) {
      console.error('Magic link error:', err);
      setError(err.message || 'Failed to send magic link');
    }
  };

  // Complete magic link sign in
  const completeMagicLink = async () => {
    setError(null);
    setLoading(true);
    try {
      await completeMagicLinkSignIn();
      push('/dashboard');
    } catch (err: any) {
      console.error('Magic link completion error:', err);
      setError(err.message || 'Failed to complete sign in');
      setLoading(false);
    }
  };

  // Sign out
  const logout = async () => {
    try {
      await signOut(auth);
      setUser(null);
      setFirebaseUser(null);
      push('/');
    } catch (err: any) {
      console.error('Logout error:', err);
      setError(err.message || 'Failed to sign out');
    }
  };

  return (
    <AuthContext.Provider value={{ 
      user, 
      firebaseUser,
      loading, 
      signInWithGoogle,
      sendMagicLink,
      completeMagicLink,
      logout, 
      emailSent,
      error,
    }}>
      {children}
    </AuthContext.Provider>
  );
};

// --- Watchlist Logic ---

export const useWatchlist = (id?: string, type?: string) => {
    const [isWatched, setIsWatched] = useState(false);

    useEffect(() => {
        if (!id) return;
        const saved = JSON.parse(localStorage.getItem('municipal_watchlist') || '[]');
        setIsWatched(saved.some((item: any) => item.id === id));
    }, [id]);

    const toggle = () => {
        if (!id || !type) return;
        const saved = JSON.parse(localStorage.getItem('municipal_watchlist') || '[]');
        const existingIndex = saved.findIndex((item: any) => item.id === id);

        let newSaved;
        if (existingIndex >= 0) {
            newSaved = saved.filter((item: any) => item.id !== id);
            setIsWatched(false);
        } else {
            newSaved = [...saved, { id, type, addedAt: new Date().toISOString() }];
            setIsWatched(true);
        }
        localStorage.setItem('municipal_watchlist', JSON.stringify(newSaved));
        
        // Dispatch event for other components to update if needed
        window.dispatchEvent(new Event('watchlist-updated'));
    };

    return { isWatched, toggle };
};

export const WatchlistToggle = ({ id, type, className = '' }: { id: string, type: 'meeting' | 'permit' | 'application' | 'plan' | 'decision', className?: string }) => {
    const { isWatched, toggle } = useWatchlist(id, type);

    return (
        <button 
            onClick={(e) => { e.stopPropagation(); toggle(); }}
            className={`p-2 rounded-full transition-all duration-200 group ${isWatched ? 'bg-yellow-50 text-yellow-500' : 'bg-gray-50 text-gray-400 hover:text-yellow-400'} ${className}`}
            title={isWatched ? "הסר מרשימת המעקב" : "הוסף לרשימת המעקב"}
        >
            {isWatched ? (
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-5 h-5">
                    <path fillRule="evenodd" d="M10.788 3.21c.448-1.077 1.976-1.077 2.424 0l2.082 5.007 5.404.433c1.164.093 1.636 1.545.749 2.305l-4.117 3.527 1.257 5.273c.271 1.136-.964 2.033-1.96 1.425L12 18.354 7.373 21.18c-.996.608-2.231-.29-1.96-1.425l1.257-5.273-4.117-3.527c-.887-.76-.415-2.212.749-2.305l5.404-.433 2.082-5.006z" clipRule="evenodd" />
                </svg>
            ) : (
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.563.045.797.77.373 1.137l-4.204 3.602a.563.563 0 00-.172.543l1.205 5.312a.563.563 0 01-.817.616l-4.632-2.825a.563.563 0 00-.594 0l-4.632 2.825a.563.563 0 01-.817-.616l1.205-5.312a.563.563 0 00-.172-.543L3.41 10.535c-.424-.367-.19-1.092.373-1.137l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                </svg>
            )}
        </button>
    );
};

// --- Layout Components ---

export const Navbar = () => {
  const path = usePathname();
  const { user, logout, loading } = useAuth();
  
  const isActive = (route: string) => {
    if (route === '/' && path === '/') return true;
    if (route !== '/' && path.startsWith(route)) return true;
    return false;
  };

  return (
    <nav className="bg-white border-b border-border sticky top-0 z-50 px-4 h-16 flex items-center shadow-sm">
        <Link href="/" className="flex items-center gap-2 no-underline text-textPrimary hover:text-primary transition-colors">
        <div className="bg-primary text-white p-1.5 rounded-lg">
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-5 h-5">
            <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 3.75h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Zm0 3h.008v.008h-.008v-.008Z" />
            </svg>
        </div>
        <span className="font-bold text-lg tracking-tight text-slate-800 hidden sm:inline">Municipal Dashboard</span>
        </Link>

        <div className="mr-8 hidden md:flex items-center gap-6">
            <Link href="/" className={`text-sm font-medium transition-colors ${isActive('/') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                ראשי
            </Link>
            <Link href="/dashboard" className={`text-sm font-medium transition-colors ${isActive('/dashboard') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                לוח בקרה
            </Link>
            <Link href="/watchlist" className={`text-sm font-medium transition-colors ${isActive('/watchlist') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                רשימת מעקב
            </Link>
            <Link href="/pricing" className={`text-sm font-medium transition-colors ${isActive('/pricing') ? 'text-primary' : 'text-textSecondary hover:text-textPrimary'}`}>
                מחירים
            </Link>
        </div>

        <div className="flex-grow" />

        <div className="flex items-center gap-3">
            {loading ? (
                <div className="w-8 h-8 border-2 border-gray-200 border-t-primary rounded-full animate-spin"></div>
            ) : user ? (
                <>
                    <Link href="/my-plan" className={`hidden sm:flex items-center gap-2 text-sm font-medium px-3 py-1.5 rounded-lg transition-colors ${isActive('/my-plan') ? 'bg-blue-50 text-primary' : 'hover:bg-gray-100 text-textSecondary'}`}>
                        {user.avatar && <img src={user.avatar} alt={user.name} className="w-5 h-5 rounded-full" />}
                        <span className="truncate max-w-[100px]">{user.name}</span>
                        <span className="text-xs bg-primary/10 text-primary px-1.5 py-0.5 rounded font-bold">{user.plan}</span>
                    </Link>
                    <button onClick={logout} className="text-sm font-medium text-red-600 hover:bg-red-50 px-4 py-2 rounded-full transition-all border border-transparent hover:border-red-100">
                        התנתקות
                    </button>
                </>
            ) : (
                <Link href="/login" className="text-sm font-medium bg-primary text-white hover:bg-primaryHover px-4 py-2 rounded-full transition-all shadow-sm">
                    כניסה
                </Link>
            )}
        </div>
    </nav>
  );
};

export const PageLayout = ({ children, title, backLink }: { children?: React.ReactNode, title?: string, backLink?: string }) => (
  <div className="min-h-screen bg-background pb-12">
    <Navbar />
    <main className="max-w-5xl mx-auto p-4 sm:p-6 lg:p-8 space-y-6 animate-fade-in">
        {backLink && (
            <Link href={backLink} className="inline-flex items-center text-sm text-textSecondary hover:text-primary mb-2 transition-colors">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor" className="w-4 h-4 ml-1">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5 21 12m0 0-7.5 7.5M21 12H3" />
                </svg>
                חזרה
            </Link>
        )}
      {children}
    </main>
  </div>
);

// --- UI Elements ---

export const Card = ({ children, className = '', onClick }: { children?: React.ReactNode, className?: string, onClick?: () => void, key?: any }) => (
  <div 
    onClick={onClick}
    className={`bg-white rounded-xl border border-border shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden ${className} ${onClick ? 'cursor-pointer' : ''}`}
  >
    {children}
  </div>
);

export const Chip = ({ label, color = 'gray', className = '' }: { label: string | number, color?: 'blue' | 'gray' | 'green' | 'orange' | 'red' | 'purple', className?: string }) => {
  const colors = {
    blue: 'bg-blue-50 text-blue-700 border-blue-100',
    gray: 'bg-gray-100 text-gray-700 border-gray-200',
    green: 'bg-green-50 text-green-700 border-green-100',
    orange: 'bg-orange-50 text-orange-800 border-orange-100',
    red: 'bg-red-50 text-red-700 border-red-100',
    purple: 'bg-purple-50 text-purple-700 border-purple-100',
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${colors[color] || colors.gray} ${className}`}>
      {label}
    </span>
  );
};

export const CopyButton = ({ text, label }: { text: string, label?: string }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button 
      onClick={handleCopy}
      className="group flex items-center gap-1.5 text-xs text-textSecondary hover:text-primary transition-colors bg-gray-50 hover:bg-blue-50 px-2 py-1 rounded border border-transparent hover:border-blue-100"
      title="העתק מזהה"
    >
        {label && <span>{label}</span>}
        <span dir="ltr" className="font-mono text-[11px] opacity-80">{text.slice(0, 8)}...</span>
        {copied ? (
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor" className="w-3.5 h-3.5 text-green-600">
                <path fillRule="evenodd" d="M16.704 4.153a.75.75 0 0 1 .143 1.052l-8 10.5a.75.75 0 0 1-1.127.075l-4.5-4.5a.75.75 0 0 1 1.06-1.06l3.894 3.893 7.48-9.817a.75.75 0 0 1 1.05-.143Z" clipRule="evenodd" />
            </svg>
        ) : (
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-3.5 h-3.5 opacity-0 group-hover:opacity-100 transition-opacity">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.666 3.888A2.25 2.25 0 0 0 13.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 0 1-.75.75H9a.75.75 0 0 1-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 0 1-2.25 2.25H6.75A2.25 2.25 0 0 1 4.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 0 1 1.927-.184" />
            </svg>
        )}
    </button>
  );
};

export const KeyValueGrid = ({ data, excludeKeys = [] }: { data: Record<string, any>, excludeKeys?: string[] }) => {
    // Filter out complex objects and excluded keys
    const entries = Object.entries(data).filter(([key, value]) => {
        if (excludeKeys.includes(key)) return false;
        if (typeof value === 'object' && value !== null) return false;
        return true;
    });

    if (entries.length === 0) return null;

    return (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-y-4 gap-x-8">
            {entries.map(([key, value]) => (
                <div key={key} className="flex flex-col">
                    <dt className="text-xs font-semibold text-textSecondary uppercase tracking-wide mb-1 flex items-center gap-1">
                        {translateKey(key)}
                        <span className="text-[10px] text-gray-400 font-normal lowercase opacity-0 group-hover:opacity-100 transition-opacity">({key})</span>
                    </dt>
                    <dd className="text-sm text-textPrimary font-medium break-words">
                        {formatValue(value, key)}
                    </dd>
                </div>
            ))}
        </div>
    );
};

// --- Helpers ---

export const formatDate = (dateStr: string | null) => {
    if (!dateStr) return 'לא ידוע';
    return new Date(dateStr).toLocaleDateString('he-IL', {
        year: 'numeric',
        month: 'long',
        day: 'numeric'
    });
};

const translateKey = (key: string): string => {
    const map: Record<string, string> = {
        city: 'עיר',
        request_id: 'מספר בקשה',
        meeting_date: 'תאריך ישיבה',
        permit_date: 'תאריך היתר',
        request_type: 'סוג בקשה',
        essence: 'מהות הבקשה',
        gush: 'גוש',
        helka: 'חלקה',
        created_at: 'נוצר ב',
        meeting_id: 'מזהה ישיבה',
        document_url: 'קישור למסמך',
        decision: 'החלטה',
        subject: 'נושא',
        applicant_name: 'שם מבקש',
        architect: 'עורך בקשה',
        published_at: 'תאריך פרסום',
        description: 'תיאור',
        plan_number: 'מספר תוכנית',
        message_type: 'סוג הודעה',
        plan_goal: 'מטרת התוכנית',
        plan_main_points: 'עיקרי התוכנית',
        applicant: 'מבקש',
        status: 'סטטוס',
        units: 'יח"ד',
        valid_until: 'בתוקף עד'
    };
    return map[key] || key;
};

const formatValue = (value: any, key: string) => {
    if (value === null || value === undefined) return '-';
    if (key.includes('date') || key.includes('created_at') || key.includes('published_at')) return formatDate(value);
    return String(value);
};

export const Skeleton = ({ className = '' }: { className?: string }) => (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
);

export const LoadingState = () => (
    <div className="grid gap-4">
        {[1, 2, 3].map(i => (
            <div key={i} className="h-32 bg-white rounded-xl border border-border p-6 shadow-sm flex flex-col gap-3">
                <Skeleton className="h-6 w-1/3" />
                <Skeleton className="h-4 w-1/4" />
                <Skeleton className="h-4 w-2/3 mt-2" />
            </div>
        ))}
    </div>
);

export const EmptyState = ({ message, icon }: { message: string, icon?: React.ReactNode }) => (
    <div className="flex flex-col items-center justify-center py-16 text-center">
        <div className="bg-gray-100 p-4 rounded-full mb-4 text-textSecondary">
            {icon || (
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor" className="w-8 h-8">
                    <path strokeLinecap="round" strokeLinejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 01-2.247 2.118H6.622a2.25 2.25 0 01-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0l-3-3m3 3l3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125z" />
                </svg>
            )}
        </div>
        <h3 className="text-lg font-medium text-textPrimary">{message}</h3>
    </div>
);
