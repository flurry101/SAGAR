import React, { useState } from 'react';
import { motion } from 'framer-motion';
import { Clock, Ship, Waves, AlertTriangle, ShieldCheck, ArrowRight, Compass, Navigation } from 'lucide-react';
import { RippleButton } from './RippleButton';
import { useAppStore } from '../../state/appStore';

export const InteractiveVoyageSimulator: React.FC = () => {
  const { setCurrentView, setScenario, setActiveAssessment } = useAppStore();
  const [beamWidth, setBeamWidth] = useState<number>(4.5);
  const [returnHour, setReturnHour] = useState<number>(16); // 16:00 IST
  const [vesselType, setVesselType] = useState<string>('Mechanized Trawler (4.5m)');

  // Deterministic SVAS Limit: beam / 4.0
  const svasLimit = beamWidth / 4.0;

  // Afternoon Swell Curve (05:00 = 0.8m, 12:00 = 1.2m, 16:00 = 2.1m, 18:00 = 2.4m)
  const getForecastWave = (hour: number) => {
    if (hour <= 8) return 0.8;
    if (hour <= 11) return 1.1;
    if (hour <= 13) return 1.3;
    if (hour <= 15) return 1.7;
    if (hour <= 17) return 2.1;
    return 2.3;
  };

  const returnWave = getForecastWave(returnHour);
  const isSevere = returnWave > svasLimit * 1.3;
  const isCaution = !isSevere && returnWave > svasLimit * 0.9;
  const isSafe = !isSevere && !isCaution;

  const handleLaunchSimulatorInAdvisory = () => {
    setScenario('SCENARIO_3_SEVERE_RETURN');
    setCurrentView('advisory');
  };

  return (
    <div className="bg-white rounded-3xl p-6 sm:p-8 border border-sagar-border shadow-soft-lg space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-sagar-borderLight pb-4">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold shadow-soft-sm">
            <Compass className="w-6 h-6 animate-spin-slow" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-extrabold text-sagar-navy">Departure & Return Time Safety Checker</h3>
              <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-800 border border-sky-200">
                Interactive Test
              </span>
            </div>
            <p className="text-xs text-slate-500">
              Select your boat size and return time to see how afternoon swells affect your safety.
            </p>
          </div>
        </div>

        {/* Live Status Badge */}
        <motion.div
          key={`${isSevere}-${isCaution}`}
          initial={{ scale: 0.9, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          className={`self-start sm:self-auto px-3.5 py-1.5 rounded-full border text-xs font-black uppercase tracking-wider flex items-center gap-2 shadow-soft-sm ${
            isSevere
              ? 'bg-rose-100 text-rose-900 border-rose-300'
              : isCaution
              ? 'bg-amber-100 text-amber-900 border-amber-300'
              : 'bg-emerald-100 text-emerald-900 border-emerald-300'
          }`}
        >
          {isSevere ? (
            <>
              <AlertTriangle className="w-4 h-4 text-rose-700 shrink-0 animate-bounce" />
              <span>DANGEROUS RETURN CONDITIONS</span>
            </>
          ) : isCaution ? (
            <>
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
              <span>MODERATE SWELL CAUTION</span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
              <span>SAFE NAVIGATION CONDITIONS</span>
            </>
          )}
        </motion.div>
      </div>

      {/* Interactive Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Left: Boat Selection */}
        <div className="space-y-3">
          <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
            <Ship className="w-4 h-4 text-sky-600" />
            <span>1. Select Boat Type:</span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: 'FRP Boat', beam: 2.2, desc: '2.2m beam' },
              { label: 'Trawler', beam: 4.5, desc: '4.5m beam' },
              { label: 'Seiner', beam: 6.0, desc: '6.0m beam' },
            ].map((v) => (
              <button
                key={v.label}
                onClick={() => {
                  setBeamWidth(v.beam);
                  setVesselType(`${v.label} (${v.beam}m)`);
                }}
                className={`p-3 rounded-2xl border text-left transition-all touch-target cursor-pointer ${
                  beamWidth === v.beam
                    ? 'bg-sagar-powder text-sky-950 border-sky-400 ring-2 ring-sky-300 shadow-soft-sm'
                    : 'bg-sagar-canvasAlt hover:bg-slate-100 text-slate-700 border-sagar-borderLight'
                }`}
              >
                <div className="font-extrabold text-xs">{v.label}</div>
                <div className="text-[11px] text-slate-500 font-mono">{v.desc}</div>
              </button>
            ))}
          </div>

          <div className="p-3 bg-sagar-canvasAlt rounded-xl border border-sagar-borderLight flex items-center justify-between text-xs font-mono">
            <span className="text-slate-600 font-sans font-medium">Safe Wave Limit for this Boat:</span>
            <strong className="text-sky-800 font-bold text-sm">{svasLimit.toFixed(2)} meters</strong>
          </div>
        </div>

        {/* Right: Return Time Slider */}
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
              <Clock className="w-4 h-4 text-sky-600" />
              <span>2. Choose Expected Return Time:</span>
            </label>
            <span className="text-xs font-mono font-extrabold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200">
              {returnHour}:00 IST
            </span>
          </div>

          <input
            type="range"
            min="6"
            max="18"
            step="1"
            value={returnHour}
            onChange={(e) => setReturnHour(parseInt(e.target.value))}
            className="w-full accent-sky-600 cursor-pointer h-2 bg-sagar-canvasAlt rounded-lg"
          />

          <div className="flex justify-between text-[11px] text-slate-500 font-mono">
            <span>06:00 (Calm 0.8m)</span>
            <span>12:00 (Mid-day 1.2m)</span>
            <span className="text-rose-700 font-bold">16:00+ (Surge 2.1m)</span>
          </div>

          <div className="p-3 bg-sagar-canvasAlt rounded-xl border border-sagar-borderLight flex items-center justify-between text-xs font-mono">
            <span className="text-slate-600 font-sans font-medium">Forecasted Wave Height at Return:</span>
            <strong className={`font-bold text-sm ${isSevere ? 'text-rose-700' : 'text-sagar-navy'}`}>
              {returnWave.toFixed(1)} meters
            </strong>
          </div>
        </div>
      </div>

      {/* Dynamic Explanation Card */}
      <motion.div
        key={`${returnHour}-${beamWidth}`}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        className={`p-4 sm:p-5 rounded-2xl border text-xs sm:text-sm flex items-start gap-4 shadow-soft-sm ${
          isSevere
            ? 'bg-rose-50 border-rose-300 text-rose-950'
            : isCaution
            ? 'bg-amber-50 border-amber-300 text-amber-950'
            : 'bg-emerald-50 border-emerald-300 text-emerald-950'
        }`}
      >
        <div
          className={`w-9 h-9 rounded-xl flex items-center justify-center shrink-0 font-bold ${
            isSevere ? 'bg-rose-100 text-rose-800' : isCaution ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
          }`}
        >
          <Waves className="w-5 h-5" />
        </div>
        <div className="flex-1 space-y-1">
          <div className="font-extrabold text-xs uppercase tracking-wide">
            {isSevere
              ? 'Safety Recommendation for Return Trip'
              : isCaution
              ? 'Caution Advisory for Return Trip'
              : 'Conditions Clear for Navigation'}
          </div>
          <p className="text-xs leading-relaxed text-slate-800 font-medium">
            {isSevere ? (
              <>
                For your <strong>{vesselType}</strong>, waves above{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong> create capsize risk. By{' '}
                <strong>{returnHour}:00 IST</strong>, afternoon waves reach{' '}
                <strong className="font-mono text-rose-700">{returnWave.toFixed(1)} m</strong>. Return before 12:00 PM to avoid dangerous water.
              </>
            ) : isCaution ? (
              <>
                Wave heights at <strong>{returnHour}:00 IST ({returnWave.toFixed(1)} m)</strong> are close to your boat limit of{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong>. Proceed with reduced speed.
              </>
            ) : (
              <>
                Wave heights during <strong>{returnHour}:00 IST ({returnWave.toFixed(1)} m)</strong> are well within your boat's safe limit of{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong>.
              </>
            )}
          </p>
        </div>
      </motion.div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
        <span className="text-xs text-slate-500 font-medium text-center sm:text-left">
          Ready to check real voyage coordinates and wind forecasts?
        </span>
        <RippleButton
          variant="primary"
          size="md"
          icon={<Navigation className="w-4 h-4" />}
          iconRight={<ArrowRight className="w-4 h-4" />}
          onClick={() => setCurrentView('chat')}
        >
          Check My Fishing Trip
        </RippleButton>
      </div>
    </div>
  );
};
