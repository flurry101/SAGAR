import React from 'react';
import { useAppStore } from '../state/appStore';
import { DEMO_SCENARIOS } from '../api/mock/scenarios';
import { WaveDivider } from '../components/common/WaveDivider';
import { ParallaxOceanHero } from '../components/common/ParallaxOceanHero';
import { InteractiveVoyageSimulator } from '../components/common/InteractiveVoyageSimulator';
import { RippleButton } from '../components/common/RippleButton';
import {
  Anchor,
  ShieldAlert,
  Compass,
  Clock,
  MapPin,
  Waves,
  ArrowRight,
  CheckCircle2,
  ShieldCheck,
  Navigation,
  Sparkles,
  Info,
  FileCheck,
  Ship,
  TrendingUp,
} from 'lucide-react';
import { motion, useScroll, useSpring, useReducedMotion, Variants } from 'framer-motion';

export const LandingPage: React.FC = () => {
  const { setCurrentView, setScenario, setActiveAssessment } = useAppStore();
  const shouldReduceMotion = useReducedMotion();
  const { scrollYProgress } = useScroll();
  const scaleX = useSpring(scrollYProgress, { stiffness: 100, damping: 30, restDelta: 0.001 });

  const handleLaunchScenario = (scenarioId: string) => {
    setScenario(scenarioId);
    const mockResponse = DEMO_SCENARIOS[scenarioId]?.mockResponse;
    if (mockResponse) {
      setActiveAssessment(mockResponse);
      setCurrentView('advisory');
    }
  };

  const containerVariants: Variants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        staggerChildren: 0.12,
      },
    },
  };

  const itemVariants: Variants = {
    hidden: { opacity: 0, y: 24 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.5, ease: 'easeOut' },
    },
  };

  return (
    <div className="space-y-16 pb-20 overflow-hidden relative">
      {/* Subtle Scroll Progress Indicator at Top */}
      {!shouldReduceMotion && (
        <motion.div
          className="fixed top-16 left-0 right-0 h-1 bg-gradient-to-r from-sky-400 via-teal-400 to-sky-600 origin-left z-50 pointer-events-none opacity-80"
          style={{ scaleX }}
        />
      )}

      {/* 1. MAJESTIC PARALLAX HERO SECTION */}
      <ParallaxOceanHero />

      {/* Wave Transition */}
      <WaveDivider fillColor="#edf5fa" secondaryFill="rgba(224, 242, 254, 0.45)" height={56} />

      {/* 2. INTERACTIVE 4D VOYAGE RISK SIMULATOR SECTION */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-60px' }}
        transition={{ duration: 0.6 }}
        className="bg-sagar-canvasAlt py-12 px-4 sm:px-6 lg:px-8 border-y border-sagar-borderLight"
      >
        <div className="max-w-7xl mx-auto space-y-8">
          <div className="text-center max-w-3xl mx-auto space-y-2">
            <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-white text-sky-900 border border-sky-200 text-xs font-bold shadow-soft-sm">
              <Sparkles className="w-3.5 h-3.5 text-sky-600" />
              <span>Interactive Decision Testbed</span>
            </div>
            <h2 className="text-2xl sm:text-4xl font-black text-sagar-navy tracking-tight">
              Test Vessel Stability & Diurnal Swell in Real Time
            </h2>
            <p className="text-sm sm:text-base text-slate-600">
              See why a 2.1m afternoon return swell is dangerous for a 2.2m beam boat, but safe for a 6.0m seiner.
            </p>
          </div>

          <InteractiveVoyageSimulator />
        </div>
      </motion.section>

      {/* Wave Transition back */}
      <WaveDivider fillColor="#f6f9fc" secondaryFill="rgba(237, 245, 250, 0.7)" height={56} flip />

      {/* 3. OPERATIONAL VOYAGE SCENARIOS SHOWCASE */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-60px' }}
        variants={containerVariants}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8"
      >
        <motion.div variants={itemVariants} className="flex flex-col sm:flex-row sm:items-end justify-between gap-3">
          <div>
            <div className="inline-flex items-center gap-1.5 text-xs font-extrabold text-sky-700 uppercase tracking-wider mb-1">
              <Sparkles className="w-4 h-4 text-sky-600" />
              <span>Verified Test Scenarios</span>
            </div>
            <h2 className="text-2xl sm:text-3xl font-black text-sagar-navy tracking-tight">
              Explore Real Operational Scenarios
            </h2>
            <p className="text-xs sm:text-sm text-slate-600 max-w-xl">
              Launch pre-computed spatio-temporal scenarios to inspect how SAGAR detects return swell hazards, geofence breaches, and multi-PFZ optimization.
            </p>
          </div>
        </motion.div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {Object.values(DEMO_SCENARIOS).map((scenario) => {
            const isSevere = scenario.id.includes('SEVERE');
            const isGeofence = scenario.id.includes('GEOFENCE');

            return (
              <motion.div
                key={scenario.id}
                variants={itemVariants}
                onClick={() => handleLaunchScenario(scenario.id)}
                whileHover={{ y: -4, scale: 1.015 }}
                whileTap={{ scale: 0.98 }}
                className={`p-6 rounded-3xl bg-white border transition-all cursor-pointer space-y-4 group shadow-soft-sm hover:shadow-soft-md touch-target ${
                  isSevere
                    ? 'hover:border-rose-300 hover:bg-rose-50/20'
                    : isGeofence
                    ? 'hover:border-amber-300 hover:bg-amber-50/20'
                    : 'hover:border-sky-300 hover:bg-sky-50/20'
                }`}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleLaunchScenario(scenario.id)}
              >
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs sm:text-sm font-extrabold text-sagar-navy group-hover:text-sky-800 transition-colors">
                    {scenario.name}
                  </span>
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-sagar-canvasAlt text-slate-700 border border-sagar-border shrink-0">
                    {scenario.badge}
                  </span>
                </div>

                <p className="text-xs text-slate-600 leading-relaxed min-h-[44px]">
                  {scenario.description}
                </p>

                <div className="pt-3 border-t border-sagar-borderLight flex items-center justify-between">
                  <span className="text-xs font-extrabold text-sky-700 group-hover:text-sky-900 flex items-center gap-1.5">
                    <span>Launch Advisory Dashboard</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </span>
                  <span className="text-[10px] font-mono font-bold text-slate-400">MapLibre + Deck.gl</span>
                </div>
              </motion.div>
            );
          })}
        </div>
      </motion.section>

      {/* 4. CORE VOYAGE SAFETY PRINCIPLES SECTION */}
      <motion.section
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-60px' }}
        variants={containerVariants}
        className="bg-sagar-canvasAlt py-14 px-4 sm:px-6 lg:px-8 border-y border-sagar-borderLight"
      >
        <div className="max-w-7xl mx-auto space-y-8">
          <motion.div variants={itemVariants} className="text-center max-w-3xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-black text-sagar-navy tracking-tight">
              Deterministic Physics & Spatio-Temporal Intelligence
            </h2>
            <p className="text-sm sm:text-base text-slate-600">
              Why static weather cards fail maritime operators — and how SAGAR provides true voyage decision support.
            </p>
          </motion.div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Pillar 1 */}
            <motion.div
              variants={itemVariants}
              className="bg-white p-6 rounded-3xl border border-sagar-border shadow-soft-sm space-y-4 hover:shadow-soft-md transition-shadow"
              whileHover={{ y: -4 }}
            >
              <div className="w-12 h-12 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
                <Clock className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-sagar-navy">4D Spatio-Temporal Matching</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Weather is not a static 2D snapshot. SAGAR models your trip across time and space — evaluating forecasted wave height, period, and wind speed at the exact future ETA of each waypoint.
              </p>
              <div className="pt-2 text-xs font-bold text-sky-700 flex items-center gap-1">
                <span>Evaluates departure, transit, & return legs</span>
              </div>
            </motion.div>

            {/* Pillar 2 */}
            <motion.div
              variants={itemVariants}
              className="bg-white p-6 rounded-3xl border border-sagar-border shadow-soft-sm space-y-4 hover:shadow-soft-md transition-shadow"
              whileHover={{ y: -4 }}
            >
              <div className="w-12 h-12 rounded-2xl bg-amber-50 text-amber-700 border border-amber-200 flex items-center justify-center font-bold">
                <Ship className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-sagar-navy">Deterministic Stability (SVAS)</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                A 1.8m wave is safe for a 30m steel trawler but dangerous for a 5m motorized canoe. SAGAR computes physical capsize limits tailored to your boat's beam width:
              </p>
              <div className="p-2.5 rounded-xl bg-sagar-canvasAlt font-mono text-xs text-sagar-navy border border-sagar-borderLight font-bold">
                max_safe_wave = beam_width / 4.0
              </div>
            </motion.div>

            {/* Pillar 3 */}
            <motion.div
              variants={itemVariants}
              className="bg-white p-6 rounded-3xl border border-sagar-border shadow-soft-sm space-y-4 hover:shadow-soft-md transition-shadow"
              whileHover={{ y: -4 }}
            >
              <div className="w-12 h-12 rounded-2xl bg-emerald-50 text-emerald-700 border border-emerald-200 flex items-center justify-center font-bold">
                <FileCheck className="w-6 h-6" />
              </div>
              <h3 className="text-base font-extrabold text-sagar-navy">Full Data Provenance</h3>
              <p className="text-xs sm:text-sm text-slate-600 leading-relaxed">
                Operators need to trust their advice. Every advisory provides complete provenance tiers (Tier 1 Live API, Tier 2 Numerical Forecast, Tier 3 Historical Baseline) with confidence ratings.
              </p>
              <div className="pt-2 text-xs font-bold text-emerald-700 flex items-center gap-1">
                <span>Expandable "See Why" evidence registry</span>
              </div>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* 5. MARITIME-READY ACCESSIBILITY BANNER */}
      <motion.section
        initial={{ opacity: 0, y: 30 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-60px' }}
        transition={{ duration: 0.6 }}
        className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8"
      >
        <div className="rounded-3xl bg-gradient-to-r from-sagar-powder via-sagar-seafoam to-sagar-aqua p-8 sm:p-10 border border-sky-200 shadow-soft-md">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
            <div className="lg:col-span-8 space-y-3 text-left">
              <span className="text-xs font-black uppercase tracking-wider text-sky-950 px-3 py-1 rounded-full bg-white/90 border border-sky-300">
                Built for Coastal Operations
              </span>
              <h3 className="text-2xl sm:text-4xl font-black text-sagar-navy tracking-tight">
                Designed for Outdoor Visibility, Mobile Touch & Regional Languages
              </h3>
              <p className="text-xs sm:text-sm text-slate-700 leading-relaxed max-w-2xl font-medium">
                SAGAR features high-contrast typography readable under bright marine sunlight, 44px+ touch targets for vessel operations, multilingual support across coastal regions, and offline progressive caching.
              </p>
            </div>
            <div className="lg:col-span-4 flex flex-col sm:flex-row lg:flex-col gap-3 justify-center">
              <RippleButton
                variant="primary"
                size="lg"
                icon={<Navigation className="w-4 h-4" />}
                onClick={() => setCurrentView('chat')}
              >
                Start Voyage Assessment
              </RippleButton>
              <RippleButton
                variant="secondary"
                size="lg"
                icon={<Ship className="w-4 h-4 text-sky-700" />}
                onClick={() => setCurrentView('vessel')}
              >
                Configure Boat Profile
              </RippleButton>
            </div>
          </div>
        </div>
      </motion.section>
    </div>
  );
};
