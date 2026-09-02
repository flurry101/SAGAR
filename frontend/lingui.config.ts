import type { LinguiConfig } from '@lingui/conf';
import { formatter } from '@lingui/format-po';

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

const config: LinguiConfig = {
  locales: [...INDIAN_LOCALES],
  sourceLocale: 'en',
  fallbackLocales: {
    default: 'en',
  },
  catalogs: [
    {
      path: '<rootDir>/src/locales/{locale}/messages',
      include: ['src'],
      exclude: ['**/node_modules/**', '**/*.d.ts', '**/*.test.{ts,tsx}', '**/dist/**'],
    },
  ],
  format: formatter({ style: 'lingui' }),
  compileNamespace: 'ts',
};

export default config;

