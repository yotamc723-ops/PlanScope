// Firebase Configuration
// Municipal Dashboard Platform

import { initializeApp } from 'firebase/app';
import { 
  getAuth, 
  GoogleAuthProvider,
  connectAuthEmulator,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  ActionCodeSettings
} from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator } from 'firebase/firestore';

// Your web app's Firebase configuration
const firebaseConfig = {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "YOUR_API_KEY",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "YOUR_PROJECT_ID.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "YOUR_PROJECT_ID",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "YOUR_PROJECT_ID.appspot.com",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "YOUR_MESSAGING_SENDER_ID",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "YOUR_APP_ID",
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);

// Initialize Firebase services
export const auth = getAuth(app);
export const db = getFirestore(app);

// Auth providers
export const googleProvider = new GoogleAuthProvider();

// Configure Google Auth Provider
googleProvider.setCustomParameters({
  prompt: 'select_account',
});

// Email link (magic link) action code settings
export const getActionCodeSettings = (): ActionCodeSettings => ({
  // URL to redirect to after email link is clicked
  url: import.meta.env.DEV 
    ? 'http://localhost:3000/login' 
    : `${window.location.origin}/login`,
  handleCodeInApp: true,
});

// Connect to emulators in development mode
if (import.meta.env.DEV) {
  // Check if we haven't already connected (prevents hot reload issues)
  const isEmulatorConnected = (auth as any)._canInitEmulator !== undefined 
    ? !(auth as any)._canInitEmulator 
    : false;

  if (!isEmulatorConnected) {
    try {
      connectAuthEmulator(auth, 'http://localhost:9099', { disableWarnings: true });
      connectFirestoreEmulator(db, 'localhost', 8080);
      console.log('🔥 Connected to Firebase Emulators (Auth: 9099, Firestore: 8080)');
    } catch (error) {
      // Emulators might already be connected
      console.log('Emulators already connected or not running');
    }
  }
}

// Email Link Auth Helper Functions
export const sendMagicLinkEmail = async (email: string): Promise<void> => {
  const actionCodeSettings = getActionCodeSettings();
  await sendSignInLinkToEmail(auth, email, actionCodeSettings);
  // Save the email locally for verification after redirect
  window.localStorage.setItem('emailForSignIn', email);
};

export const isMagicLinkSignIn = (): boolean => {
  return isSignInWithEmailLink(auth, window.location.href);
};

export const completeMagicLinkSignIn = async (): Promise<void> => {
  if (!isSignInWithEmailLink(auth, window.location.href)) {
    throw new Error('Not a valid sign-in link');
  }

  // Get the email from localStorage
  let email = window.localStorage.getItem('emailForSignIn');
  
  if (!email) {
    // If email is not in localStorage, prompt user
    email = window.prompt('Please provide your email for confirmation');
  }
  
  if (!email) {
    throw new Error('Email is required to complete sign-in');
  }

  // Complete sign-in
  await signInWithEmailLink(auth, email, window.location.href);
  
  // Clear the email from storage
  window.localStorage.removeItem('emailForSignIn');
  
  // Clean up the URL
  window.history.replaceState({}, document.title, window.location.pathname);
};

export default app;
