import React from 'react';
import { useAppStore, AppLanguage } from '../../state/appStore';
import { Globe } from 'lucide-react';

const SUPPORTED_LANGUAGES: { code: AppLanguage; label: string; regional: string }[] = [
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
  return null;
};
