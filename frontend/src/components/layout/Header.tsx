import React, { useState } from 'react';
import { useAppStore, AppView } from '../../state/appStore';
import { LanguageSelector } from '../common/LanguageSelector';
import { Anchor, Compass, ShieldAlert, Ship, BookOpen, History, UserCheck, Menu, X, AlertTriangle, Waves } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trans, useLingui } from '@lingui/react/macro';

export const Header: React.FC = () => {
  const { currentView, setCurrentView, isAuthenticated, userProfile, setSosModalOpen } = useAppStore();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);
  const { t } = useLingui();

  const navItems: { id: AppView; label: string; shortLabel: string; icon: React.ReactNode }[] = [
    { id: 'landing', label: t`Overview`, shortLabel: t`Overview`, icon: <Compass className="w-4 h-4 shrink-0" /> },
    { id: 'chat', label: t`Trip Planner`, shortLabel: t`Trip Planner`, icon: <Anchor className="w-4 h-4 shrink-0" /> },
    { id: 'advisory', label: t`Advisory Dashboard`, shortLabel: t`Advisory`, icon: <ShieldAlert className="w-4 h-4 shrink-0" /> },
    { id: 'conditions', label: 'Live Conditions', shortLabel: 'Conditions', icon: <Waves className="w-4 h-4 shrink-0" /> },
    { id: 'knowledge', label: t`Marine Knowledge`, shortLabel: t`Knowledge`, icon: <BookOpen className="w-4 h-4 shrink-0" /> },
  ];

  const profileMenuItems: { id: AppView; label: string; icon: React.ReactNode }[] = [
    { id: 'auth', label: isAuthenticated ? t`Profile` : t`Sign In`, icon: <UserCheck className="w-4 h-4 shrink-0" /> },
    { id: 'vessel', label: t`Vessel Profile`, icon: <Ship className="w-4 h-4 shrink-0" /> },
    { id: 'history', label: t`Voyage History`, icon: <History className="w-4 h-4 shrink-0" /> },
  ];

  const fullDisplayName = isAuthenticated ? userProfile?.name || t`Marine Operator` : t`Sign In`;
  const shortDisplayName = isAuthenticated ? (userProfile?.name || t`Operator`) : t`Sign In`;

  return (
    <header className="w-full bg-white/95 backdrop-blur-md border-b border-sagar-border sticky top-0 z-40 shadow-soft-sm">
      <div className="w-full max-w-[1440px] mx-auto px-3 sm:px-4 lg:px-6">
        <div className="flex items-center justify-between h-16 gap-2 sm:gap-3 min-w-0">
          {/* 1. Brand Identity */}
          <div
            onClick={() => setCurrentView('landing')}
            className="flex items-center gap-2.5 sm:gap-3 cursor-pointer group select-none shrink-0"
            role="button"
            tabIndex={0}
            onKeyDown={(e) => e.key === 'Enter' && setCurrentView('landing')}
            aria-label={t`SAGAR Home`}
          >
            <img
              src="/sagar-logo.png"
              alt="SAGAR Logo"
              className="w-9 h-9 sm:w-10 sm:h-10 object-contain rounded-full shadow-soft-sm group-hover:scale-105 transition-transform shrink-0"
            />
            <div className="shrink-0">
              <div className="flex items-center gap-1.5">
                <span className="font-black text-lg sm:text-xl text-sagar-navy tracking-tight">SAGAR</span>
                <span className="text-[9px] sm:text-[10px] uppercase font-extrabold tracking-wider px-2 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200 shrink-0">
                  <Trans>Decision Support</Trans>
                </span>
              </div>
              <p className="text-[10px] text-sagar-textMuted font-medium hidden md:block">
                <Trans>4D Marine Voyage Safety System</Trans>
              </p>
            </div>
          </div>

          {/* 2. Desktop Navigation: Wide screens (>= 1380px) with full labels */}
          <nav className="hidden min-[1380px]:flex flex-1 items-center justify-center gap-0.5 bg-sagar-canvasAlt/90 p-1.5 rounded-2xl border border-sagar-borderLight min-w-0">
            {navItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-all duration-150 whitespace-nowrap cursor-pointer shrink min-w-0 ${
                    active
                      ? 'text-sky-950 font-extrabold'
                      : 'text-slate-600 hover:text-sagar-navy hover:bg-white/60'
                  }`}
                >
                  {active && (
                    <motion.div
                      layoutId="activeNavPillDesktop"
                      className="absolute inset-0 bg-white rounded-xl shadow-soft-sm border border-sagar-border/70"
                      transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                    />
                  )}
                  <span className="relative z-10 flex items-center gap-1.5 min-w-0">
                    {item.icon}
                    <span>{item.label}</span>
                  </span>
                </button>
              );
            })}
          </nav>

          {/* 3. Compact Laptop Navigation (1180px to 1379px): Short labels */}
          <nav className="hidden min-[1180px]:flex min-[1380px]:hidden flex-1 items-center justify-center gap-0.5 bg-sagar-canvasAlt/90 p-1 rounded-2xl border border-sagar-borderLight min-w-0">
            {navItems.map((item) => {
              const active = currentView === item.id;
              return (
                <button
                  key={item.id}
                  onClick={() => setCurrentView(item.id)}
                  title={item.label}
                  className={`relative flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-bold transition-all duration-150 whitespace-nowrap cursor-pointer shrink min-w-0 ${
                    active
                      ? 'text-sky-950 font-extrabold bg-white shadow-soft-sm border border-sagar-border/70'
                      : 'text-slate-600 hover:text-sagar-navy hover:bg-white/60'
                  }`}
                >
                  <span className="relative z-10 flex items-center gap-1 min-w-0">
                    {item.icon}
                    <span>{item.shortLabel}</span>
                  </span>
                </button>
              );
            })}
          </nav>

          {/* 4. Right Controls: SOS, Language & Profile Access */}
          <div className="flex items-center gap-2 sm:gap-2.5 shrink-0 ml-auto">
            {/* SOS Emergency Button */}
            <motion.button
              whileHover={{ scale: 1.04 }}
              whileTap={{ scale: 0.96 }}
              onClick={() => setSosModalOpen(true)}
              className="flex items-center gap-1.5 px-3 sm:px-3.5 py-1.5 sm:py-2 rounded-full bg-[#d63031] hover:bg-red-600 text-white text-xs font-black shadow-[0_2px_10px_rgba(214,48,49,0.35)] transition-all touch-target cursor-pointer shrink-0 border border-red-400/40"
              title={t`Coast Guard Emergency Distress (1554)`}
              aria-label={t`Emergency Distress SOS 1554`}
            >
              <AlertTriangle className="w-3.5 h-3.5 stroke-[2.5]" />
              <span className="tracking-wide">SOS 1554</span>
            </motion.button>

            {/* Language Selector */}
            <div className="hidden sm:block shrink-0">
              <LanguageSelector />
            </div>

            {/* Profile Button - Never Squeezed or Clipped */}
            <div className="relative shrink-0">
              <motion.button
                whileHover={{ y: -1, scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => setProfileMenuOpen((prev) => !prev)}
                className="flex items-center gap-2 px-3 py-2 rounded-xl bg-white hover:bg-sagar-canvasAlt text-sagar-navy text-xs font-extrabold border border-sagar-border transition-all shadow-soft-sm touch-target cursor-pointer shrink-0"
                title={fullDisplayName}
                aria-label={fullDisplayName}
              >
                <div className="w-6 h-6 rounded-full bg-sagar-powder text-sky-700 flex items-center justify-center shrink-0 border border-sky-200">
                  <UserCheck className="w-3.5 h-3.5" />
                </div>
                <span className="hidden lg:inline whitespace-nowrap font-extrabold text-sagar-navy">
                  {fullDisplayName}
                </span>
                <span className="hidden sm:inline lg:hidden whitespace-nowrap font-extrabold text-sagar-navy">
                  {shortDisplayName}
                </span>
              </motion.button>

              <AnimatePresence>
                {profileMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -8, scale: 0.98 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -8, scale: 0.98 }}
                    transition={{ duration: 0.15 }}
                    className="absolute right-0 top-full mt-2 w-56 rounded-2xl border border-sagar-border bg-white p-2 shadow-soft-lg z-50"
                  >
                    {profileMenuItems.map((item) => (
                      <button
                        key={item.id}
                        onClick={() => {
                          setCurrentView(item.id);
                          setProfileMenuOpen(false);
                        }}
                        className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-bold text-slate-700 hover:bg-sagar-canvasAlt hover:text-sagar-navy text-left"
                      >
                        {item.icon}
                        <span>{item.label}</span>
                      </button>
                    ))}
                  </motion.div>
                )}
              </AnimatePresence>
            </div>

            {/* Mobile/Tablet Menu Button (shows on < 1180px) */}
            <div className="min-[1180px]:hidden flex items-center shrink-0">
              <button
                onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
                className="p-2 rounded-xl bg-white text-slate-700 hover:text-sagar-navy border border-sagar-border touch-target flex items-center justify-center shadow-soft-sm cursor-pointer shrink-0"
                aria-label={t`Toggle navigation menu`}
              >
                {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Mobile Drawer with AnimatePresence */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            transition={{ duration: 0.2 }}
            className="min-[1180px]:hidden border-t border-sagar-border bg-white px-4 pt-3 pb-5 space-y-2 shadow-soft-lg overflow-hidden"
          >
            <div className="pb-2 mb-2 border-b border-sagar-borderLight space-y-2">
              <button
                onClick={() => {
                  setSosModalOpen(true);
                  setMobileMenuOpen(false);
                }}
                className="w-full flex items-center justify-center gap-2 px-4 py-2.5 rounded-full bg-[#d63031] hover:bg-red-600 text-white text-xs font-black shadow-md touch-target cursor-pointer border border-red-400/40"
              >
                <AlertTriangle className="w-4 h-4 stroke-[2.5]" />
                <span>SOS 1554 - <Trans>Coast Guard Emergency</Trans></span>
              </button>
              <div className="sm:hidden">
                <LanguageSelector />
              </div>
            </div>
            {navItems.map((item) => (
              <button
                key={item.id}
                onClick={() => {
                  setCurrentView(item.id);
                  setMobileMenuOpen(false);
                }}
                className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl text-sm font-bold touch-target cursor-pointer ${
                  currentView === item.id
                    ? 'bg-sagar-powder text-sky-950 border border-sky-300'
                    : 'text-slate-700 hover:bg-sagar-canvasAlt'
                }`}
              >
                {item.icon}
                <span>{item.label}</span>
              </button>
            ))}
            <div className="pt-2 border-t border-sagar-borderLight space-y-2">
              {profileMenuItems.map((item) => (
                <button
                  key={item.id}
                  onClick={() => {
                    setCurrentView(item.id);
                    setMobileMenuOpen(false);
                  }}
                  className="w-full flex items-center justify-start gap-3 px-4 py-3 bg-sagar-canvasAlt text-sky-950 rounded-xl text-xs font-extrabold border border-sagar-border touch-target cursor-pointer"
                >
                  {item.icon}
                  <span>{item.label}</span>
                </button>
              ))}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </header>
  );
};
