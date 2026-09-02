import React from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';
import { Anchor, Compass, ShieldAlert, Navigation, ArrowRight, Sparkles, Waves, ShieldCheck, MapPin, Wind, Ship, ArrowDownRight } from 'lucide-react';
import { RippleButton } from './RippleButton';
import { useAppStore } from '../../state/appStore';
import { Trans, useLingui } from '@lingui/react/macro';

export const ParallaxOceanHero: React.FC = () => {
  const { setCurrentView, setScenario } = useAppStore();
  const shouldReduceMotion = useReducedMotion();
  const { scrollY } = useScroll();
  const { t } = useLingui();

  // Multi-layer parallax scroll transforms
  const yBg = useTransform(scrollY, [0, 600], [0, 90]);
  const yWave1 = useTransform(scrollY, [0, 600], [0, 45]);
  const yWave2 = useTransform(scrollY, [0, 600], [0, 20]);
  const yContent = useTransform(scrollY, [0, 600], [0, -15]);
  const opacityHero = useTransform(scrollY, [0, 500], [1, 0.9]);

  const handleLaunchScenario = (scenarioId: string) => {
    setScenario(scenarioId);
    setCurrentView('advisory');
  };

  const voyageSteps = [
    { label: t`Origin`, time: 'Mangalore', status: t`Harbor Base`, icon: <Anchor className="w-3.5 h-3.5" /> },
    { label: t`Departure`, time: '05:00 IST', status: t`Calm (0.8m)`, icon: <Navigation className="w-3.5 h-3.5 text-emerald-600" /> },
    { label: t`Outbound`, time: '07:30 IST', status: t`30km Corridor`, icon: <Ship className="w-3.5 h-3.5 text-sky-600" /> },
    { label: t`Operational Area`, time: '10:00 IST', status: t`Active PFZ`, icon: <Sparkles className="w-3.5 h-3.5 text-teal-600" /> },
    { label: t`Return Transit`, time: '16:00 IST', status: t`Swell Evaluated`, icon: <Waves className="w-3.5 h-3.5 text-amber-600" /> },
    { label: t`Safe Arrival`, time: '18:00 IST', status: t`SVAS Verified`, icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> },
  ];

  return (
    <section className="relative overflow-hidden pt-6 sm:pt-10 pb-6 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto select-none">
      {/* Background Parallax Layer 1: Nautical Depth Contours & Compass Grid */}
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yBg }}
        className="absolute inset-0 pointer-events-none z-0 select-none opacity-40"
        aria-hidden="true"
      >
        <svg className="w-full h-full stroke-sky-300/40 fill-none" viewBox="0 0 1200 600">
          <circle cx="980" cy="180" r="160" strokeWidth="1.2" strokeDasharray="4 6" />
          <circle cx="980" cy="180" r="260" strokeWidth="1" strokeDasharray="6 8" />
          <circle cx="980" cy="180" r="380" strokeWidth="0.75" strokeDasharray="8 10" />
          <line x1="980" y1="0" x2="980" y2="600" strokeWidth="1" strokeDasharray="3 5" opacity="0.4" />
          <line x1="500" y1="180" x2="1200" y2="180" strokeWidth="1" strokeDasharray="3 5" opacity="0.4" />
          <path d="M 980,140 L 980,220 M 940,180 L 1020,180" strokeWidth="1.5" stroke="#0284c7" opacity="0.6" />
        </svg>
      </motion.div>

      {/* Main Hero Content */}
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yContent, opacity: opacityHero }}
        className="relative z-10 space-y-8"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8 items-center">
          {/* Left Column: Brand & Value Prop */}
          <div className="lg:col-span-7 space-y-5 text-left">
            {/* Majestic SAGAR Badge */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center gap-2.5 px-3.5 py-1.5 rounded-full bg-white/95 backdrop-blur-md border border-sky-200 text-sky-950 text-xs font-extrabold shadow-soft-sm tracking-wide"
            >
              <img src="/sagar-logo.png" alt="SAGAR" className="w-5 h-5 rounded-full object-contain shrink-0" />
              <span>SAGAR — <Trans>Marine Safety & Decision Support</Trans></span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
            </motion.div>

            {/* Majestic SAGAR Heading */}
            <div className="space-y-3">
              <h1 className="text-3xl sm:text-5xl font-black text-sagar-navy tracking-tight leading-[1.1]">
                <span className="bg-gradient-to-r from-sky-700 via-sky-600 to-teal-700 bg-clip-text text-transparent">
                  SAGAR
                </span>
                <span className="block text-xl sm:text-3xl font-extrabold text-slate-800 mt-1">
                  <Trans>Voice-First Multilingual Marine Safety Assistant</Trans>
                </span>
              </h1>

              <p className="text-sm sm:text-base text-slate-700 leading-relaxed font-normal max-w-2xl">
                <Trans>SAGAR is a voice-first, multilingual marine safety assistant for fishermen, researchers and coastal authorities, combining ocean forecasting, geofencing, and explainable advisory logic into a single operational decision-support system.</Trans>
              </p>
            </div>

            {/* Interactive CTAs with Ripple Physics */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <RippleButton
                variant="primary"
                size="lg"
                icon={<Navigation className="w-5 h-5" />}
                iconRight={<ArrowRight className="w-5 h-5" />}
                onClick={() => setCurrentView('chat')}
              >
                <Trans>Plan Maritime Voyage</Trans>
              </RippleButton>

              <RippleButton
                variant="secondary"
                size="lg"
                icon={<ShieldAlert className="w-5 h-5 text-amber-600" />}
                onClick={() => handleLaunchScenario('SCENARIO_3_SEVERE_RETURN')}
              >
                <Trans>Simulate Afternoon Swell Surge</Trans>
              </RippleButton>
            </div>

            {/* Live Marine Features Strip */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-sagar-borderLight max-w-xl text-left">
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-sky-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-sky-800 tracking-wider"><Trans>Spatial Engine</Trans></div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5"><Trans>4D Coastal Grids</Trans></div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-teal-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-teal-800 tracking-wider"><Trans>Stability Rule</Trans></div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">Beam / 4.0 SVAS</div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-indigo-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-indigo-800 tracking-wider"><Trans>Provenance</Trans></div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5"><Trans>Tier 1–3 Verified</Trans></div>
              </div>
            </div>
          </div>

          {/* Right Column: Dynamic 4D Journey Simulator Card */}
          <div className="lg:col-span-5">
            <div className="relative bg-white/95 backdrop-blur-sm rounded-3xl p-6 sm:p-7 border border-sagar-border shadow-soft-lg space-y-4 overflow-hidden">
              {/* Top Badge */}
              <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-sky-500 animate-ping" />
                  <span className="text-xs font-extrabold text-sagar-navy"><Trans>Voyage Spatio-Temporal Journey</Trans></span>
                </div>
                <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200">
                  12.87°N, 74.84°E
                </span>
              </div>

              {/* Journey Stages with Animated Progression */}
              <div className="space-y-2.5">
                {/* 1. Departure */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-sagar-canvasAlt border border-sagar-borderLight hover:border-sky-200 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-emerald-100 text-emerald-800 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    05:00
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
                      <span><Trans>Harbor Departure</Trans></span>
                      <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-300">
                        <Trans>SAFE (0.8m Wave)</Trans>
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate"><Trans>Calm morning coastal sea state</Trans></p>
                  </div>
                </div>

                {/* 2. Outbound Transit */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-sagar-canvasAlt border border-sagar-borderLight hover:border-sky-200 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    07:30
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
                      <span><Trans>Outbound Transit (30 km)</Trans></span>
                      <span className="text-[10px] font-extrabold text-sky-800 bg-sky-100 px-2 py-0.5 rounded-full border border-sky-300">
                        <Trans>FAVOURABLE</Trans>
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate"><Trans>Transit corridor clear, wind 12 km/h</Trans></p>
                  </div>
                </div>

                {/* 3. Target PFZ Ground */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-sagar-canvasAlt border border-sagar-borderLight hover:border-teal-200 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    10:00
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
                      <span><Trans>Target PFZ Ground</Trans></span>
                      <span className="text-[10px] font-extrabold text-teal-800 bg-teal-100 px-2 py-0.5 rounded-full border border-teal-300">
                        <Trans>AGGREGATION ACTIVE</Trans>
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate"><Trans>Thermal front convergence active</Trans></p>
                  </div>
                </div>

                {/* 4. Return Hazard */}
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-rose-50 border border-rose-300 shadow-soft-sm">
                  <div className="w-8 h-8 rounded-xl bg-rose-200 text-rose-900 flex items-center justify-center font-mono font-black text-xs shrink-0">
                    16:00
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-extrabold text-rose-950">
                      <span><Trans>Return Leg Swell Surge</Trans></span>
                      <span className="text-[10px] font-black text-rose-900 bg-rose-100 px-2 py-0.5 rounded-full border border-rose-300">
                        <Trans>SEVERE HAZARD (2.1m)</Trans>
                      </span>
                    </div>
                    <p className="text-[11px] text-rose-800 font-medium leading-tight mt-0.5">
                      <Trans>Afternoon wave surge exceeds trawler stability beam limit (1.1m)</Trans>
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Insight Banner */}
              <div className="bg-sagar-powder/80 p-3.5 rounded-2xl border border-sky-200 text-xs text-sky-950 flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-sky-700 shrink-0" />
                <span>
                  <strong>SAGAR Reasoning:</strong> <Trans>Warns of return hazards before departure.</Trans>
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* Dedicated Voyage Journey Workflow Strip: PLAN → TRAVEL → MONITOR → RETURN SAFELY */}
        <div className="bg-white/90 backdrop-blur-md rounded-3xl p-5 sm:p-6 border border-sagar-border shadow-soft-md space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-sagar-borderLight pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-sky-900 bg-sagar-powder px-3 py-1 rounded-full border border-sky-200">
                <Trans>Continuous Voyage Safety Lifecycle</Trans>
              </span>
              <span className="text-xs font-extrabold text-sagar-navy">
                PLAN → TRAVEL → MONITOR → RETURN SAFELY
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium hidden md:inline">
              <Trans>End-to-end spatio-temporal vessel safety matching</Trans>
            </span>
          </div>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            {voyageSteps.map((step, idx) => (
              <div
                key={idx}
                className="p-3 rounded-2xl bg-sagar-canvasAlt/80 border border-sagar-borderLight hover:border-sky-300 hover:bg-sagar-powder/30 transition-all space-y-1.5 text-left"
              >
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-mono font-bold text-sky-800 bg-white px-2 py-0.5 rounded-md border border-sagar-borderLight">
                    0{idx + 1}
                  </span>
                  {step.icon}
                </div>
                <div className="font-extrabold text-xs text-sagar-navy truncate">{step.label}</div>
                <div className="text-[11px] font-semibold text-slate-700">{step.time}</div>
                <div className="text-[10px] text-slate-500 font-medium truncate">{step.status}</div>
              </div>
            ))}
          </div>
        </div>
      </motion.div>
    </section>
  );
};
