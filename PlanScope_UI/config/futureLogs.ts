/**
 * Centralized switches for console logging across dashboard features.
 * Toggle flags to enable/disable noisy logs while debugging.
 */
export const futureLogs = {
  // UI blocks
  meetingsBlock: true,
  permitsBlock: true,
  applicationsBlock: true,
  plansBlock: true,
  dashboardSummary: false,

  // User/account
  authFlow: false,
  onboarding: false,
  watchlist: true,
  subscriptions: false,

  // Data + API
  firestoreReads: false,
  firestoreWrites: false,
  apiRequests: false,
  emailBroadcasts: false,

  // Payments
  payments: false,
  paymentWebhooks: false,
} as const;

export type FutureLogKey = keyof typeof futureLogs;

/**
 * Helper to check if logging is enabled for a given feature.
 */
export function isLogEnabled(feature: FutureLogKey): boolean {
  return Boolean(futureLogs[feature]);
}

/**
 * Safe log wrapper that respects feature switches.
 */
export function logFeature(feature: FutureLogKey, ...args: unknown[]): void {
  if (isLogEnabled(feature)) {
    // eslint-disable-next-line no-console
    console.log(`[${feature}]`, ...args);
  }
}

