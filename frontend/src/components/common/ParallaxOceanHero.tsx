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
    { label: 'Fishing Ground', time: '10:00 IST', status: 'Active PFZ', icon: <Sparkles className="w-3.5 h-3.5 text-teal-600" /> },
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
            {/* Majestic SAGAR Badge */}
            <motion.div
              initial={{ opacity: 0, y: -10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-flex items-center gap-2.5 px-4 py-2 rounded-full bg-white/95 backdrop-blur-md border border-sky-200 text-sky-950 text-xs font-extrabold shadow-soft-sm tracking-wide"
            >
              <div className="w-5 h-5 rounded-full bg-sky-600 text-white flex items-center justify-center font-bold">
                <Anchor className="w-3 h-3" />
              </div>
              <span>SAGAR — Marine Voyage Decision Support</span>
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-ping" />
            </motion.div>

            {/* Majestic SAGAR Heading */}
            <div className="space-y-3">
              <h1 className="text-4xl sm:text-6xl font-black text-sagar-navy tracking-tight leading-[1.08]">
                <span className="bg-gradient-to-r from-sky-700 via-sky-600 to-teal-700 bg-clip-text text-transparent">
                  SAGAR
                </span>
                <span className="block text-2xl sm:text-4xl font-extrabold text-slate-800 mt-1">
                  4D Spatio-Temporal Voyage Safety & Decision Support
                </span>
              </h1>

              <p className="text-base sm:text-lg text-slate-700 leading-relaxed font-normal max-w-2xl">
                Calm morning seas at departure can turn into hazardous afternoon swell surges during return transit. SAGAR evaluates your entire voyage across <strong className="text-sagar-navy font-bold">exact future transit hours at every waypoint</strong>, matching live ocean forecasts against your boat's physical beam stability limits.
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
                Plan Fishing Voyage
              </RippleButton>

              <RippleButton
                variant="secondary"
                size="lg"
                icon={<ShieldAlert className="w-5 h-5 text-amber-600" />}
                onClick={() => handleLaunchScenario('SCENARIO_3_SEVERE_RETURN')}
              >
                Simulate Afternoon Swell Surge
              </RippleButton>
            </div>

            {/* Live Marine Features Strip */}
            <div className="grid grid-cols-3 gap-3 pt-4 border-t border-sagar-borderLight max-w-xl text-left">
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-sky-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-sky-800 tracking-wider">Spatial Engine</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">4D Coastal Grids</div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-teal-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-teal-800 tracking-wider">Stability Rule</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">Beam / 4.0 SVAS</div>
              </div>
              <div className="p-3.5 bg-white/90 rounded-2xl border border-sagar-borderLight shadow-soft-sm hover:border-indigo-300 transition-colors">
                <div className="text-[10px] font-extrabold uppercase text-indigo-800 tracking-wider">Provenance</div>
                <div className="text-xs sm:text-sm font-extrabold text-sagar-navy mt-0.5">Tier 1–3 Verified</div>
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
                  <span className="text-xs font-extrabold text-sagar-navy">Voyage Spatio-Temporal Journey</span>
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
                      <span>Harbor Departure</span>
                      <span className="text-[10px] font-extrabold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-300">
                        SAFE (0.8m Wave)
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate">Calm morning coastal sea state</p>
                  </div>
                </div>

                {/* 2. Outbound Transit */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-sagar-canvasAlt border border-sagar-borderLight hover:border-sky-200 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-sky-100 text-sky-800 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    07:30
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
                      <span>Outbound Transit (30 km)</span>
                      <span className="text-[10px] font-extrabold text-sky-800 bg-sky-100 px-2 py-0.5 rounded-full border border-sky-300">
                        FAVOURABLE
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate">Transit corridor clear, wind 12 km/h</p>
                  </div>
                </div>

                {/* 3. Target PFZ Ground */}
                <div className="flex items-center gap-3 p-3 rounded-2xl bg-sagar-canvasAlt border border-sagar-borderLight hover:border-teal-200 transition-colors">
                  <div className="w-8 h-8 rounded-xl bg-teal-100 text-teal-800 flex items-center justify-center font-mono font-bold text-xs shrink-0">
                    10:00
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
                      <span>Target PFZ Ground</span>
                      <span className="text-[10px] font-extrabold text-teal-800 bg-teal-100 px-2 py-0.5 rounded-full border border-teal-300">
                        AGGREGATION ACTIVE
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate">Thermal front convergence active</p>
                  </div>
                </div>

                {/* 4. Return Hazard */}
                <div className="flex items-center gap-3 p-3.5 rounded-2xl bg-rose-50 border border-rose-300 shadow-soft-sm">
                  <div className="w-8 h-8 rounded-xl bg-rose-200 text-rose-900 flex items-center justify-center font-mono font-black text-xs shrink-0">
                    16:00
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="flex items-center justify-between text-xs font-extrabold text-rose-950">
                      <span>Return Leg Swell Surge</span>
                      <span className="text-[10px] font-black text-rose-900 bg-rose-100 px-2 py-0.5 rounded-full border border-rose-300">
                        SEVERE HAZARD (2.1m)
                      </span>
                    </div>
                    <p className="text-[11px] text-rose-800 font-medium leading-tight mt-0.5">
                      Afternoon wave surge exceeds trawler stability beam limit (1.1m)
                    </p>
                  </div>
                </div>
              </div>

              {/* Bottom Insight Banner */}
              <div className="bg-sagar-powder/80 p-3.5 rounded-2xl border border-sky-200 text-xs text-sky-950 flex items-center gap-2.5">
                <ShieldCheck className="w-4 h-4 text-sky-700 shrink-0" />
                <span>
                  <strong>SAGAR Reasoning:</strong> Warns of return hazards before departure.
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
                Continuous Voyage Safety Lifecycle
              </span>
              <span className="text-xs font-extrabold text-sagar-navy">
                PLAN → TRAVEL → MONITOR → RETURN SAFELY
              </span>
            </div>
            <span className="text-[11px] text-slate-500 font-medium hidden md:inline">
              End-to-end spatio-temporal vessel safety matching
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
