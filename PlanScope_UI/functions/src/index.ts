/**
 * Firebase Cloud Functions - 2nd Generation (v2)
 * Municipal Dashboard Platform
 */

import { setGlobalOptions } from "firebase-functions/v2";
import { beforeUserCreated } from "firebase-functions/v2/identity";
import * as admin from "firebase-admin";
import { FieldValue } from "firebase-admin/firestore";

// Initialize Firebase Admin
admin.initializeApp();
const db = admin.firestore();

// Set global options for all functions
setGlobalOptions({
  maxInstances: 10,
  region: "europe-west1",
});

/**
 * Triggered before a new user is created in Firebase Auth.
 * Creates the user document in Firestore with the schema defined in firestore-schema.md
 */
export const onUserCreate = beforeUserCreated(async (event) => {
  const user = event.data;

  if (!user) {
    console.error("No user data in event");
    return;
  }

  const uid = user.uid;
  const email = user.email || "";
  const displayName = user.displayName || null;
  const photoURL = user.photoURL || null;

  // Determine auth provider
  let authProvider: "password" | "google.com" = "password";
  if (user.providerData && user.providerData.length > 0) {
    const providerId = user.providerData[0].providerId;
    if (providerId === "google.com") {
      authProvider = "google.com";
    }
  }

  // Create user document with schema from firestore-schema.md
  const userDoc = {
    // Authentication
    uid,
    email,
    displayName,
    photoURL,
    authProvider,

    // Subscription (defaults for new users)
    subscriptionPlan: "free" as const,
    subscriptionStatus: "active" as const,
    subscriptionStartDate: null,
    subscriptionEndDate: null,

    // Email Preferences
    emailNotifications: true,
    marketingEmails: false,

    // Metadata
    createdAt: FieldValue.serverTimestamp(),
    lastLoginAt: FieldValue.serverTimestamp(),
    onboardingCompleted: false,
    preferredCity: null,
  };

  try {
    await db.collection("users").doc(uid).set(userDoc);
    console.log(`Created user document for ${uid} (${email})`);
  } catch (error) {
    console.error(`Failed to create user document for ${uid}:`, error);
    throw error;
  }
});
