import React from 'react';
import { motion, useScroll, useTransform, useReducedMotion } from 'framer-motion';
import { Anchor, Compass, ShieldAlert, Navigation, ArrowRight, Sparkles, Waves, ShieldCheck, MapPin, Wind, Ship, ArrowDownRight } from 'lucide-react';
import { RippleButton } from './RippleButton';
import { useAppStore } from '../../state/appStore';

export const ParallaxOceanHero: React.FC = () => {
  const { setCurrentView, setScenario } = useAppStore();
  const shouldReduceMotion = useReducedMotion();
  const { scrollY } = useScroll();

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
    { label: 'Origin', time: 'Mangalore', status: 'Harbor Base', icon: <Anchor className="w-3.5 h-3.5" /> },
    { label: 'Departure', time: '05:00 IST', status: 'Calm (0.8m)', icon: <Navigation className="w-3.5 h-3.5 text-emerald-600" /> },
    { label: 'Outbound', time: '07:30 IST', status: '30km Corridor', icon: <Ship className="w-3.5 h-3.5 text-sky-600" /> },
    { label: 'Operational Area', time: '10:00 IST', status: 'Active PFZ', icon: <Sparkles className="w-3.5 h-3.5 text-teal-600" /> },
    { label: 'Return Transit', time: '16:00 IST', status: 'Swell Evaluated', icon: <Waves className="w-3.5 h-3.5 text-amber-600" /> },
    { label: 'Safe Arrival', time: '18:00 IST', status: 'SVAS Verified', icon: <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" /> },
  ];

  return (
    <section className="relative overflow-hidden pt-8 sm:pt-14 pb-24 px-4 sm:px-6 lg:px-8 max-w-7xl mx-auto select-none">
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

      {/* Layer 2: Multi-Layered Fluid Animated SVG Waves at Bottom */}
      <div className="absolute inset-x-0 bottom-0 pointer-events-none z-0 overflow-hidden h-44 opacity-80">
        {/* Wave Layer 1: Deep Slow Current */}
        <div className="absolute inset-x-0 bottom-0 w-[200%] h-36 animate-wave-drift-slow">
          <svg className="w-full h-full fill-sky-200/40" viewBox="0 0 1440 160" preserveAspectRatio="none">
            <path d="M0,48 C150,96 350,0 500,48 C650,96 850,0 1000,48 C1150,96 1350,0 1440,48 L1440,160 L0,160 Z"></path>
          </svg>
        </div>

        {/* Wave Layer 2: Mid-level Undulating Swell */}
        <div className="absolute inset-x-0 bottom-0 w-[200%] h-28 animate-wave-drift-fast opacity-90">
          <svg className="w-full h-full fill-sky-100/70" viewBox="0 0 1440 160" preserveAspectRatio="none">
            <path d="M0,64 C200,16 400,112 600,64 C800,16 1000,112 1200,64 C1350,32 1400,80 1440,64 L1440,160 L0,160 Z"></path>
          </svg>
        </div>

        {/* Wave Layer 3: Foam Crest Line */}
        <div className="absolute inset-x-0 bottom-0 w-[200%] h-16 animate-wave-drift-slow opacity-60">
          <svg className="w-full h-full fill-sagar-canvas" viewBox="0 0 1440 160" preserveAspectRatio="none">
            <path d="M0,80 C240,40 480,120 720,80 C960,40 1200,120 1440,80 L1440,160 L0,160 Z"></path>
          </svg>
        </div>
      </div>

      {/* Main Hero Content */}
      <motion.div
        style={{ y: shouldReduceMotion ? 0 : yContent, opacity: opacityHero }}
        className="relative z-10 space-y-10"
      >
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
          {/* Left Column: Brand & Value Prop */}
          <div className="lg:col-span-7 space-y-6 text-left">
            {/* Operational Badge */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-white/95 backdrop-blur-md border border-sky-200 text-sky-950 text-xs font-extrabold shadow-soft-sm tracking-wide"
            >
              <div className="w-5 h-5 rounded-full bg-sky-600 text-white flex items-center justify-center font-bold">
                <Anchor className="w-3 h-3" />
              </div>
              <span>SAGAR — Coastal Marine Safety System</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
            </motion.div>

            {/* Clear Actionable Heading */}
            <div className="space-y-3">
              <h1 className="text-4xl sm:text-5xl font-black text-sagar-navy tracking-tight leading-[1.1]">
                <span className="bg-gradient-to-r from-sky-700 via-sky-600 to-teal-700 bg-clip-text text-transparent">
                  Know If Your Fishing Trip Is Safe
                </span>
                <span className="block text-2xl sm:text-3xl font-extrabold text-slate-800 mt-1.5">
                  Before You Leave Harbor
                </span>
              </h1>

              <p className="text-base sm:text-lg text-slate-700 leading-relaxed font-normal max-w-2xl">
                Morning waters may look calm, but dangerous afternoon swells can cause small boats to capsize during return trips. SAGAR checks sea forecasts for your exact return time and warns you if wave heights exceed your boat's safe limits.
              </p>
            </div>

            {/* Direct Action CTAs */}
            <div className="flex flex-wrap items-center gap-4 pt-2">
              <RippleButton
                variant="primary"
                size="lg"
                icon={<Navigation className="w-5 h-5" />}
                iconRight={<ArrowRight className="w-5 h-5" />}
                onClick={() => setCurrentView('chat')}
              >
                Check Trip Safety
              </RippleButton>

              <RippleButton
                variant="secondary"
                size="lg"
                icon={<Ship className="w-5 h-5 text-sky-700" />}
                onClick={() => setCurrentView('vessel')}
              >
                Set Boat Dimensions
              </RippleButton>
            </div>

            {/* Core Capability Strip */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-sagar-borderLight max-w-xl text-left">
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm">
                <div className="text-[10px] font-extrabold uppercase text-sky-800 tracking-wider">Sea Forecasts</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">Wave & Tide Alerts</div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm">
                <div className="text-[10px] font-extrabold uppercase text-teal-800 tracking-wider">Boat Stability</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">Capsize Wave Limits</div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm">
                <div className="text-[10px] font-extrabold uppercase text-indigo-800 tracking-wider">Voice First</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">10+ Indian Languages</div>
              </div>
            </div>
          </div>

          {/* Right Column: 3-Second Maritime Safety Verdict Card */}
          <div className="lg:col-span-5">
            <div className="relative bg-white rounded-3xl p-6 sm:p-7 border border-sagar-border shadow-soft-lg space-y-4 overflow-hidden text-left">
              {/* Card Header */}
              <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
                <div className="flex items-center gap-2">
                  <ShieldAlert className="w-4 h-4 text-amber-600" />
                  <span className="text-xs font-black text-sagar-navy uppercase tracking-wider">
                    Instant Voyage Verdict
                  </span>
                </div>
                <span className="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-amber-50 text-amber-900 border border-amber-200">
                  Live Coastal Sample
                </span>
              </div>

              {/* 3-Second Rule: 1. Is it safe? */}
              <div className="p-3.5 bg-amber-50/90 border border-amber-300 rounded-2xl space-y-1">
                <div className="text-[10px] font-black text-amber-800 uppercase tracking-wider">1. Is it safe?</div>
                <div className="text-sm font-black text-amber-950 flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 animate-pulse shrink-0" />
                  <span>CAUTION: Safe to depart, but dangerous after 1:00 PM</span>
                </div>
              </div>

              {/* 3-Second Rule: 2. Why? */}
              <div className="p-3.5 bg-sagar-canvasAlt border border-sagar-borderLight rounded-2xl space-y-1.5">
                <div className="text-[10px] font-black text-slate-500 uppercase tracking-wider">2. Why?</div>
                <div className="text-xs text-slate-800 leading-relaxed space-y-1">
                  <div>🌊 <strong>Afternoon sea swell:</strong> Waves climb to <strong className="text-rose-700">2.1m</strong> off Malpe by 16:00.</div>
                  <div>🚤 <strong>Your boat limit:</strong> Safe wave limit for your FRP boat is <strong className="text-sagar-navy">1.1m</strong>.</div>
                </div>
              </div>

              {/* 3-Second Rule: 3. What to do next? */}
              <div className="p-3.5 bg-emerald-50/80 border border-emerald-300 rounded-2xl space-y-1">
                <div className="text-[10px] font-black text-emerald-800 uppercase tracking-wider">3. What should I do?</div>
                <div className="text-xs font-extrabold text-emerald-950">
                  ⏰ Depart at 05:00 AM • Return to dock before 12:00 PM
                </div>
              </div>

              {/* Quick Action Buttons */}
              <div className="pt-2 flex items-center gap-2.5">
                <button
                  type="button"
                  onClick={() => setCurrentView('chat')}
                  className="flex-1 py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-soft-sm flex items-center justify-center gap-2 transition-all touch-target cursor-pointer"
                >
                  <Navigation className="w-3.5 h-3.5" />
                  <span>Check My Port & Boat</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleLaunchScenario('SCENARIO_3_SEVERE_RETURN')}
                  className="py-3 px-3.5 rounded-xl bg-sagar-canvasAlt hover:bg-slate-100 text-sagar-navy font-bold text-xs border border-sagar-border shadow-soft-sm transition-all touch-target cursor-pointer"
                  title="Inspect detailed return swell advisory"
                >
                  View Details
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Voyage Journey Workflow Strip: PLAN → DEPART → FISH → RETURN SAFELY */}
        <div className="bg-white/90 backdrop-blur-md rounded-3xl p-5 sm:p-6 border border-sagar-border shadow-soft-md space-y-4">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-sagar-borderLight pb-3">
            <div className="flex items-center gap-2">
              <span className="text-xs font-extrabold uppercase tracking-wider text-sky-900 bg-sagar-powder px-3 py-1 rounded-full border border-sky-200">
                Simple 4-Step Safety Flow
              </span>
              <span className="text-xs font-extrabold text-sagar-navy">
                CHECK WEATHER → SET RETURN TIME → FISH SAFELY → DOCK BEFORE SWELL
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium hidden md:inline">
              Protecting lives & vessels at sea
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
