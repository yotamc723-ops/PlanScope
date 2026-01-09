// Firebase Configuration
// Municipal Dashboard Platform

import { initializeApp, getApps, getApp } from 'firebase/app';
import {
  getAuth,
  GoogleAuthProvider,
  connectAuthEmulator,
  sendSignInLinkToEmail,
  isSignInWithEmailLink,
  signInWithEmailLink,
  ActionCodeSettings
} from 'firebase/auth';
import { getFirestore, connectFirestoreEmulator, initializeFirestore } from 'firebase/firestore';

// Your web app's Firebase configuration
// Your web app's Firebase configuration
const firebaseConfig = import.meta.env.DEV ? {
  apiKey: "demo-api-key",
  authDomain: "demo-municipal-dashboard.firebaseapp.com",
  projectId: "demo-municipal-dashboard",
  storageBucket: "demo-municipal-dashboard.firebasestorage.app",
  messagingSenderId: "123456789",
  appId: "1:123456789:web:demo123456",
} : {
  apiKey: import.meta.env.VITE_FIREBASE_API_KEY || "AIzaSyB32G0F_yqN9heaJN0pjiVlTJkAusRlrTs",
  authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN || "municipal-dashboard-prod.firebaseapp.com",
  projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID || "municipal-dashboard-prod",
  storageBucket: import.meta.env.VITE_FIREBASE_STORAGE_BUCKET || "municipal-dashboard-prod.firebasestorage.app",
  messagingSenderId: import.meta.env.VITE_FIREBASE_MESSAGING_SENDER_ID || "447281245428",
  appId: import.meta.env.VITE_FIREBASE_APP_ID || "1:447281245428:web:2242a4d7bda6f55cb942a1",
};

// Initialize Firebase
const app = getApps().length > 0 ? getApp() : initializeApp(firebaseConfig);

// Initialize Auth
export const auth = getAuth(app);

// Initialize Firestore with strict Long Polling for Emulators
let firestoreDb;

if (import.meta.env.DEV) {
  // 1. Force Long Polling to avoid "net::ERR_EMPTY_RESPONSE"
  firestoreDb = initializeFirestore(app, {
    experimentalForceLongPolling: true,
  });

  // 2. Connect to Emulators immediately (Strict 127.0.0.1)
  // Check if already connected to avoid hot-reload errors
  // Note: SDK usually handles this, but safe to wrap
  try {
    connectAuthEmulator(auth, 'http://127.0.0.1:9099', { disableWarnings: true });
    connectFirestoreEmulator(firestoreDb, '127.0.0.1', 8080);
    console.log('🔥 [Firebase] Connected to Emulators (Auth: 9099, Firestore: 8080) with Long Polling');
  } catch (error) {
    console.log('⚠️ [Firebase] Emulators already connected', error);
  }

} else {
  // Production initialization
  firestoreDb = getFirestore(app);
}

export const db = firestoreDb;

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
