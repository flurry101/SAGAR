/**
 * SAGAR Marine Decision-Support System
 * Brand Text Sanitizer & Formatting Utilities
 * 
 * Ensures all user-facing text, backend responses, advisory strings,
 * and error messages adhere to the SAGAR product identity.
 */

/**
 * Sanitizes any raw string from backend responses or mock data
 * to replace legacy codenames or internal labels with SAGAR terminology.
 */
export function sanitizeSagarText(text?: string | null): string {
  if (!text) return '';
  return text
    .replace(/ORCA/gi, 'SAGAR')
    .replace(/PathFinder/gi, 'SAGAR')
    .replace(/Smart India Hackathon/gi, 'Maritime Safety Authority')
    .replace(/SIH[0-9]*/gi, '')
    .replace(/M[1-5]\b/g, '')
    .trim();
}

/**
 * Standardized SAGAR safety disclaimer.
 */
export const SAGAR_SAFETY_DISCLAIMER =
  'SAGAR provides advisory decision support to assist fishers in voyage planning. It does not replace official marine weather bulletins from IMD or INCOIS. The final navigation and safety decision always rests with the vessel skipper.';

/**
 * Formats advisory disclaimers to ensure uniform, professional decision-support phrasing.
 */
export function formatSagarDisclaimer(rawDisclaimer?: string | null): string {
  if (!rawDisclaimer || rawDisclaimer.includes('ORCA') || rawDisclaimer.includes('PathFinder')) {
    return SAGAR_SAFETY_DISCLAIMER;
  }
  return sanitizeSagarText(rawDisclaimer);
}

/**
 * Formats advisory recommendation text safely.
 */
export function formatSagarAdvisory(text?: string | null): string {
  if (!text) return 'Safety assessment completed. Review trip timeline and conditions before departure.';
  return sanitizeSagarText(text);
}
