import React from 'react';
import { useAppStore, AppLanguage } from '../../state/appStore';
import { Globe } from 'lucide-react';

const SUPPORTED_LANGUAGES: { code: AppLanguage; label: string; regional: string }[] = [
  { code: 'en', label: 'English', regional: 'English' },
  { code: 'kn', label: 'Kannada', regional: 'ಕನ್ನಡ' },
  { code: 'ta', label: 'Tamil', regional: 'தமிழ்' },
  { code: 'te', label: 'Telugu', regional: 'తెలుగు' },
  { code: 'ml', label: 'Malayalam', regional: 'മലയാളം' },
  { code: 'hi', label: 'Hindi', regional: 'हिन्दी' },
  { code: 'mr', label: 'Marathi', regional: 'मराठी' },
  { code: 'gu', label: 'Gujarati', regional: 'ગુજરાતી' },
  { code: 'bn', label: 'Bengali', regional: 'বাংলা' },
  { code: 'or', label: 'Odia', regional: 'ଓଡ଼ିଆ' },
  { code: 'pa', label: 'Punjabi', regional: 'ਪੰਜਾਬੀ' },
];

export const LanguageSelector: React.FC = () => {
  const { selectedLanguage, setLanguage } = useAppStore();

  return (
    <div className="flex items-center gap-1 bg-white hover:bg-sagar-canvasAlt border border-sagar-border rounded-xl px-2.5 py-1.5 text-xs text-sagar-navy shadow-soft-sm focus-within:border-sky-500 transition-colors">
      <Globe className="w-3.5 h-3.5 text-sky-600 shrink-0" />
      <select
        value={selectedLanguage}
        onChange={(e) => setLanguage(e.target.value as AppLanguage)}
        className="bg-transparent text-xs font-bold text-sagar-navy focus:outline-none cursor-pointer pr-1 appearance-none"
        aria-label="Select regional language"
      >
        {SUPPORTED_LANGUAGES.map((lang) => (
          <option key={lang.code} value={lang.code} className="bg-white text-sagar-navy font-sans">
            {lang.label} ({lang.regional})
          </option>
        ))}
      </select>
    </div>
  );
};
