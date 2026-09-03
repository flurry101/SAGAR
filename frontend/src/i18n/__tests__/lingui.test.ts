import {
  INDIAN_LOCALES,
  LANGUAGE_REGISTRY,
  isRtlLocale,
  detectInitialLocale,
  SupportedLocale,
} from '../lingui';

export function runLinguiTests() {
  console.log('Running Lingui Runtime Tests...');

  // 1. Locales count
  if (INDIAN_LOCALES.length !== 23) {
    throw new Error(`Expected 23 locales, got ${INDIAN_LOCALES.length}`);
  }

  // 2. Coastal languages check
  const coastalCodes: SupportedLocale[] = ['kn', 'ta', 'ml', 'te', 'mr', 'gu', 'bn', 'or', 'kok'];
  for (const code of coastalCodes) {
    const info = LANGUAGE_REGISTRY[code];
    if (!info || !info.isCoastal || !info.regional) {
      throw new Error(`Invalid coastal language registration for ${code}`);
    }
  }

  // 3. RTL check
  if (!isRtlLocale('ur') || !isRtlLocale('ks') || !isRtlLocale('sd')) {
    throw new Error('RTL language check failed for Urdu, Kashmiri, or Sindhi');
  }
  if (isRtlLocale('kn') || isRtlLocale('ta') || isRtlLocale('en')) {
    throw new Error('LTR language incorrectly flagged as RTL');
  }

  // 4. Initial locale detection fallback
  const initial = detectInitialLocale();
  if (!INDIAN_LOCALES.includes(initial)) {
    throw new Error(`Invalid initial locale: ${initial}`);
  }

  console.log('ALL Lingui Runtime Tests PASSED!');
  return true;
}

