import { i18n } from '@lingui/core';

export const INDIAN_LOCALES = [
  'en',    // English (Source)
  'hi',    // Hindi
  'kn',    // Kannada (Coastal - Karnataka)
  'ta',    // Tamil (Coastal - Tamil Nadu, Puducherry)
  'te',    // Telugu (Coastal - Andhra Pradesh)
  'ml',    // Malayalam (Coastal - Kerala, Lakshadweep)
  'mr',    // Marathi (Coastal - Maharashtra, Goa)
  'gu',    // Gujarati (Coastal - Gujarat, Daman)
  'bn',    // Bengali (Coastal - West Bengal, Andaman)
  'or',    // Odia (Coastal - Odisha)
  'kok',   // Konkani (Coastal - Goa, Maharashtra, Karnataka)
  'ur',    // Urdu (RTL)
  'pa',    // Punjabi
  'as',    // Assamese
  'mai',   // Maithili
  'sat',   // Santali
  'ks',    // Kashmiri (RTL)
  'ne',    // Nepali
  'sd',    // Sindhi (RTL)
  'doi',   // Dogri
  'mni',   // Manipuri (Meitei)
  'brx',   // Bodo
  'sa',    // Sanskrit
] as const;

export type SupportedLocale = (typeof INDIAN_LOCALES)[number];

export interface LanguageInfo {
  code: SupportedLocale;
  label: string;
  regional: string;
  isCoastal: boolean;
  coastalRegion?: string;
  isRtl?: boolean;
}

export const LANGUAGE_REGISTRY: Record<SupportedLocale, LanguageInfo> = {
  en: { code: 'en', label: 'English', regional: 'English', isCoastal: true, coastalRegion: 'All Ports & Universal' },
  kn: { code: 'kn', label: 'Kannada', regional: 'ಕನ್ನಡ', isCoastal: true, coastalRegion: 'Karnataka (Mangalore, Malpe, Karwar)' },
  ta: { code: 'ta', label: 'Tamil', regional: 'தமிழ்', isCoastal: true, coastalRegion: 'Tamil Nadu & Puducherry (Chennai, Tuticorin)' },
  ml: { code: 'ml', label: 'Malayalam', regional: 'മലയാളം', isCoastal: true, coastalRegion: 'Kerala & Lakshadweep (Cochin, Vizhinjam)' },
  te: { code: 'te', label: 'Telugu', regional: 'తెలుగు', isCoastal: true, coastalRegion: 'Andhra Pradesh (Visakhapatnam, Kakinada)' },
  mr: { code: 'mr', label: 'Marathi', regional: 'मराठी', isCoastal: true, coastalRegion: 'Maharashtra (Mumbai, Ratnagiri)' },
  gu: { code: 'gu', label: 'Gujarati', regional: 'ગુજરાતી', isCoastal: true, coastalRegion: 'Gujarat & Daman (Kandla, Porbandar, Veraval)' },
  bn: { code: 'bn', label: 'Bengali', regional: 'বাংলা', isCoastal: true, coastalRegion: 'West Bengal & Andaman (Kolkata, Haldia, Digha)' },
  or: { code: 'or', label: 'Odia', regional: 'ଓଡ଼ିଆ', isCoastal: true, coastalRegion: 'Odisha (Paradip, Gopalpur, Dhamra)' },
  kok: { code: 'kok', label: 'Konkani', regional: 'कोंकणी', isCoastal: true, coastalRegion: 'Goa, Maharashtra & Karnataka (Mormugao, Karwar)' },
  hi: { code: 'hi', label: 'Hindi', regional: 'हिन्दी', isCoastal: true, coastalRegion: 'National & Coastal Inland Waterways' },
  ur: { code: 'ur', label: 'Urdu', regional: 'اردو', isCoastal: true, coastalRegion: 'Andhra, Maharashtra & Coastal Hubs', isRtl: true },
  pa: { code: 'pa', label: 'Punjabi', regional: 'ਪੰਜਾਬੀ', isCoastal: false },
  as: { code: 'as', label: 'Assamese', regional: 'অসমীয়া', isCoastal: false },
  mai: { code: 'mai', label: 'Maithili', regional: 'मैथिली', isCoastal: false },
  sat: { code: 'sat', label: 'Santali', regional: 'ᱥᱟᱱᱛᱟᱲᱤ', isCoastal: false },
  ks: { code: 'ks', label: 'Kashmiri', regional: 'کٲشُر / कॉशुर', isCoastal: false, isRtl: true },
  ne: { code: 'ne', label: 'Nepali', regional: 'नेपाली', isCoastal: false },
  sd: { code: 'sd', label: 'Sindhi', regional: 'سنڌي / सिन्धी', isCoastal: true, coastalRegion: 'Kutch / Gujarat Coastal', isRtl: true },
  doi: { code: 'doi', label: 'Dogri', regional: 'डोगरी', isCoastal: false },
  mni: { code: 'mni', label: 'Manipuri', regional: 'মৈতৈলোন্', isCoastal: false },
  brx: { code: 'brx', label: 'Bodo', regional: 'बड़ो', isCoastal: false },
  sa: { code: 'sa', label: 'Sanskrit', regional: 'संस्कृतम्', isCoastal: false },
};

export const RTL_LOCALES = new Set<SupportedLocale>(['ur', 'ks', 'sd']);

export function isRtlLocale(locale: string): boolean {
  return RTL_LOCALES.has(locale as SupportedLocale);
}

// In-memory catalog cache
const loadedCatalogs = new Set<string>();

/**
 * Dynamically loads and activates the catalog for the requested locale.
 */
export async function dynamicActivate(locale: SupportedLocale): Promise<void> {
  try {
    if (!INDIAN_LOCALES.includes(locale)) {
      locale = 'en';
    }

    if (!loadedCatalogs.has(locale)) {
      try {
        const catalog = await import(`../locales/${locale}/messages.po`);
        i18n.load(locale, catalog.messages || catalog.default || {});
        loadedCatalogs.add(locale);
      } catch (err) {
        console.warn(`[Lingui] Could not import messages for ${locale}, fallback to empty/en`, err);
        i18n.load(locale, {});
      }
    }

    i18n.activate(locale);

    // Apply document attributes for mobile browsers & screen readers
    if (typeof document !== 'undefined') {
      document.documentElement.setAttribute('lang', locale);
      document.documentElement.setAttribute('dir', isRtlLocale(locale) ? 'rtl' : 'ltr');
    }

    if (typeof localStorage !== 'undefined') {
      localStorage.setItem('sagar_user_locale', locale);
    }
  } catch (error) {
    console.error(`[Lingui] Failed to activate locale: ${locale}`, error);
    if (locale !== 'en') {
      await dynamicActivate('en');
    }
  }
}

/**
 * Mobile-friendly initial locale detection.
 * Checks localStorage first, then browser navigator languages matching Indian codes, fallback to 'en'.
 */
export function detectInitialLocale(): SupportedLocale {
  if (typeof window === 'undefined') return 'en';

  const stored = localStorage.getItem('sagar_user_locale');
  if (stored && INDIAN_LOCALES.includes(stored as SupportedLocale)) {
    return stored as SupportedLocale;
  }

  // Detect from browser/mobile device settings
  const navLanguages = navigator.languages || [navigator.language];
  for (const rawLang of navLanguages) {
    if (!rawLang) continue;
    const cleanLang = rawLang.toLowerCase().split('-')[0] as SupportedLocale;
    if (INDIAN_LOCALES.includes(cleanLang)) {
      return cleanLang;
    }
  }

  return 'en';
}

export { i18n };

