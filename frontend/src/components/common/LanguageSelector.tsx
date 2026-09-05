import React, { useState } from 'react';
import { useAppStore } from '../../state/appStore';
import { LANGUAGE_REGISTRY, INDIAN_LOCALES, SupportedLocale, LanguageInfo } from '../../i18n/lingui';
import { Globe, Check, Anchor, Search, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

export const LanguageSelector: React.FC = () => {
  const { selectedLanguage, setLanguage } = useAppStore();
  const [isOpen, setIsOpen] = useState(false);
  const [activeTab, setActiveTab] = useState<'coastal' | 'all'>('coastal');
  const [searchQuery, setSearchQuery] = useState('');
  const { t } = useLingui();

  const currentLangInfo = LANGUAGE_REGISTRY[selectedLanguage] || LANGUAGE_REGISTRY.en;

  const coastalLanguages = (INDIAN_LOCALES as readonly SupportedLocale[])
    .map((code) => LANGUAGE_REGISTRY[code])
    .filter((info): info is LanguageInfo => Boolean(info?.isCoastal));

  const allLanguages = (INDIAN_LOCALES as readonly SupportedLocale[])
    .map((code) => LANGUAGE_REGISTRY[code])
    .filter((info): info is LanguageInfo => Boolean(info));

  const displayedLanguages = (activeTab === 'coastal' ? coastalLanguages : allLanguages).filter((item) => {
    if (!searchQuery.trim()) return true;
    const q = searchQuery.toLowerCase();
    return (
      item.label.toLowerCase().includes(q) ||
      item.regional.toLowerCase().includes(q) ||
      item.code.toLowerCase().includes(q) ||
      (item.coastalRegion && item.coastalRegion.toLowerCase().includes(q))
    );
  });

  const handleSelect = (code: SupportedLocale) => {
    setLanguage(code);
    setIsOpen(false);
    setSearchQuery('');
  };

  return (
    <div className="relative">
      {/* Trigger Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen((prev) => !prev)}
        className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-white hover:bg-sagar-canvasAlt text-sagar-navy text-xs font-bold border border-sagar-border transition-all shadow-soft-sm cursor-pointer shrink-0"
        title={t`Change language`}
        aria-label={t`Language Selector`}
      >
        <Globe className="w-3.5 h-3.5 text-sky-600 shrink-0" />
        <span className="font-extrabold text-sagar-navy whitespace-nowrap">{currentLangInfo.regional}</span>
        <span className="text-[10px] text-slate-400 font-semibold hidden lg:inline">({currentLangInfo.label})</span>
      </motion.button>

      {/* Modal / Popup with AnimatePresence */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs z-50 sm:hidden"
            />

            {/* Content Container (Bottom-sheet on mobile, dropdown card on desktop) */}
            <motion.div
              initial={{ opacity: 0, y: 12, scale: 0.96 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: 12, scale: 0.96 }}
              transition={{ duration: 0.16 }}
              className="fixed inset-x-3 bottom-4 max-h-[85vh] sm:absolute sm:inset-auto sm:right-0 sm:top-full sm:mt-2 sm:w-[420px] sm:max-h-[520px] bg-white rounded-3xl border border-sagar-border shadow-soft-xl z-50 flex flex-col overflow-hidden text-sagar-navy"
            >
              {/* Header */}
              <div className="p-4 border-b border-sagar-borderLight bg-gradient-to-r from-sky-50 to-white flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <div className="w-8 h-8 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
                    <Globe className="w-4 h-4" />
                  </div>
                  <div>
                    <h3 className="text-sm font-extrabold text-sagar-navy"><Trans>Select Language / ಭಾಷೆ</Trans></h3>
                    <p className="text-[11px] text-slate-500"><Trans>22 Indian Official Languages & Coastal Ports</Trans></p>
                  </div>
                </div>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1.5 rounded-lg hover:bg-slate-100 text-slate-400 hover:text-slate-600"
                  aria-label={t`Close`}
                >
                  <X className="w-4 h-4" />
                </button>
              </div>

              {/* Tabs: Coastal vs All 22 */}
              <div className="flex p-2 bg-slate-100/70 border-b border-sagar-borderLight gap-1">
                <button
                  onClick={() => setActiveTab('coastal')}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'coastal'
                      ? 'bg-white text-sky-900 shadow-soft-sm'
                      : 'text-slate-600 hover:text-sagar-navy'
                  }`}
                >
                  <Anchor className="w-3.5 h-3.5 text-sky-600" />
                  <span><Trans>Coastal Ports & States</Trans></span>
                </button>
                <button
                  onClick={() => setActiveTab('all')}
                  className={`flex-1 flex items-center justify-center gap-1.5 py-1.5 px-2 rounded-xl text-xs font-bold transition-all ${
                    activeTab === 'all'
                      ? 'bg-white text-sky-900 shadow-soft-sm'
                      : 'text-slate-600 hover:text-sagar-navy'
                  }`}
                >
                  <Globe className="w-3.5 h-3.5 text-sky-600" />
                  <span><Trans>All 22 Languages</Trans></span>
                </button>
              </div>

              {/* Search Bar */}
              <div className="p-2.5 border-b border-sagar-borderLight">
                <div className="relative flex items-center">
                  <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3" />
                  <input
                    type="text"
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    placeholder={t`Search language, script, or coastal port...`}
                    className="w-full bg-slate-50 border border-slate-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-sagar-navy focus:outline-none focus:border-sky-500"
                  />
                </div>
              </div>

              {/* Languages List */}
              <div className="flex-1 overflow-y-auto p-2 space-y-1.5 max-h-[340px] scrollbar-thin">
                {displayedLanguages.map((item) => {
                  const isSelected = selectedLanguage === item.code;
                  return (
                    <button
                      key={item.code}
                      onClick={() => handleSelect(item.code)}
                      className={`w-full flex items-center justify-between p-2.5 rounded-2xl text-left transition-all group cursor-pointer ${
                        isSelected
                          ? 'bg-sky-50 border border-sky-300 text-sky-950'
                          : 'hover:bg-slate-50 border border-transparent'
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div
                          className={`w-7 h-7 rounded-xl flex items-center justify-center font-bold text-xs ${
                            isSelected ? 'bg-sky-600 text-white' : 'bg-slate-100 text-slate-600 group-hover:bg-sky-100 group-hover:text-sky-700'
                          }`}
                        >
                          {item.code.toUpperCase()}
                        </div>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-extrabold text-sm text-sagar-navy">{item.regional}</span>
                            <span className="text-xs text-slate-500 font-medium">({item.label})</span>
                            {item.isRtl && (
                              <span className="text-[9px] px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-bold">
                                RTL
                              </span>
                            )}
                          </div>
                          {item.coastalRegion && (
                            <p className="text-[10px] text-sky-700 font-medium">{item.coastalRegion}</p>
                          )}
                        </div>
                      </div>

                      {isSelected && <Check className="w-4 h-4 text-sky-600 shrink-0" />}
                    </button>
                  );
                })}

                {displayedLanguages.length === 0 && (
                  <div className="p-6 text-center text-xs text-slate-400">
                    <Trans>No matching language found for "{searchQuery}".</Trans>
                  </div>
                )}
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};
