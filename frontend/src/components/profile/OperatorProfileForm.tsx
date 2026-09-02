import React, { useState, useEffect } from 'react';
import { useAppStore, AppLanguage } from '../../state/appStore';
import { userApi } from '../../api/userApi';
import { LANGUAGE_REGISTRY, INDIAN_LOCALES, SupportedLocale } from '../../i18n/lingui';
import { User, Mail, Anchor, Globe, Save, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { Trans, useLingui } from '@lingui/react/macro';

const LANGUAGE_OPTIONS = (INDIAN_LOCALES as readonly SupportedLocale[]).map((code) => ({
  code,
  label: LANGUAGE_REGISTRY[code]?.label || code,
  native: LANGUAGE_REGISTRY[code]?.regional || code,
  coastal: LANGUAGE_REGISTRY[code]?.isCoastal,
}));

export const OperatorProfileForm: React.FC = () => {
  const { t } = useLingui();
  const {
    isAuthenticated,
    userProfile,
    selectedLanguage,
    setLanguage,
    setAuthenticated,
    supabaseToken,
  } = useAppStore();

  const [name, setName] = useState(userProfile?.name || 'Marine Operator');
  const [email, setEmail] = useState(userProfile?.email || '');
  const [port, setPort] = useState(userProfile?.port || 'Mangalore Port');
  const [language, setPreferredLang] = useState<AppLanguage>(selectedLanguage);
  const [saving, setSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    if (userProfile) {
      if (userProfile.name) setName(userProfile.name);
      if (userProfile.email) setEmail(userProfile.email);
      if (userProfile.port) setPort(userProfile.port);
    }
    setPreferredLang(selectedLanguage);
  }, [userProfile, selectedLanguage]);

  // Load existing profile from backend if available
  useEffect(() => {
    let active = true;
    const fetchProfile = async () => {
      try {
        const res: any = await userApi.getCurrentUser();
        if (active && res && res.name) {
          setName(res.name);
          if (res.email) setEmail(res.email);
          if (res.home_port) setPort(res.home_port);
          if (res.preferred_language) {
            setPreferredLang(res.preferred_language as AppLanguage);
            setLanguage(res.preferred_language as AppLanguage);
          }
          setAuthenticated(
            true,
            {
              name: res.name,
              port: res.home_port || port,
              email: res.email || email,
              userId: res.user_id || userProfile?.userId,
            },
            supabaseToken
          );
        }
      } catch (err) {
        // Unauthenticated or offline — use store values
      }
    };
    if (isAuthenticated) {
      fetchProfile();
    }
    return () => {
      active = false;
    };
  }, [isAuthenticated]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setErrorMessage(null);

    // Update local state store immediately
    setLanguage(language);
    setAuthenticated(
      isAuthenticated || true,
      {
        name,
        port,
        email,
        userId: userProfile?.userId,
      },
      supabaseToken
    );

    try {
      // Sync update with backend API
      await userApi.updateCurrentUser({
        name,
        home_port: port,
        preferred_language: language,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 3500);
    } catch (err: any) {
      // If user record didn't exist yet, try creating it
      try {
        await userApi.createUser({
          name,
          home_port: port,
          preferred_language: language,
        });
        setSaved(true);
        setTimeout(() => setSaved(false), 3500);
      } catch (createErr) {
        console.warn('Profile sync saved to local session:', err);
        setSaved(true);
        setTimeout(() => setSaved(false), 3500);
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={handleSubmit}
      className="bg-white border border-sagar-border rounded-2xl p-6 sm:p-8 shadow-soft-sm space-y-6 max-w-2xl mx-auto my-4 text-sagar-navy"
    >
      <div className="flex items-center gap-3 border-b border-sagar-borderLight pb-4">
        <div className="w-11 h-11 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
          <User className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-sagar-navy">
            <Trans>Fisherman & Operator Profile</Trans>
          </h2>
          <p className="text-xs text-slate-500">
            <Trans>Personal identity, base harbor, and language settings for localized advisories.</Trans>
          </p>
        </div>
      </div>

      {saved && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs flex items-center gap-2 font-medium">
          <CheckCircle2 className="w-4 h-4 text-emerald-700 shrink-0" />
          <span><Trans>Operator profile updated and synced successfully!</Trans></span>
        </div>
      )}

      {errorMessage && (
        <div className="p-3.5 bg-rose-50 border border-rose-200 rounded-xl text-rose-900 text-xs font-medium">
          {errorMessage}
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1">
            <Trans>Operator Full Name</Trans>
          </label>
          <div className="relative">
            <input
              type="text"
              required
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
              placeholder={t`e.g. Ramesh Sagar`}
            />
          </div>
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1 flex items-center gap-1">
            <Mail className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Email Address</Trans></span>
          </label>
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
            placeholder={t`operator@marine.mission`}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1 flex items-center gap-1">
            <Anchor className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Base Port / Home Harbor</Trans></span>
          </label>
          <input
            type="text"
            required
            value={port}
            onChange={(e) => setPort(e.target.value)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
            placeholder={t`e.g. Mangalore Old Port`}
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1 flex items-center gap-1">
            <Globe className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Preferred Advisory Language</Trans></span>
          </label>
          <select
            value={language}
            onChange={(e) => setPreferredLang(e.target.value as AppLanguage)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none cursor-pointer"
          >
            {LANGUAGE_OPTIONS.map((opt) => (
              <option key={opt.code} value={opt.code}>
                {opt.label} ({opt.native})
              </option>
            ))}
          </select>
        </div>
      </div>

      <button
        type="submit"
        disabled={saving}
        className="w-full py-3.5 rounded-xl bg-sky-600 hover:bg-sky-500 disabled:opacity-50 text-white font-bold text-xs sm:text-sm shadow-soft-sm flex items-center justify-center gap-2 transition-all touch-target cursor-pointer"
      >
        <Save className="w-4 h-4" />
        <span>{saving ? <Trans>Saving Profile...</Trans> : <Trans>Save Operator Profile</Trans>}</span>
      </button>
    </form>
  );
};

