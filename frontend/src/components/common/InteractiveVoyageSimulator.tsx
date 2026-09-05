import React, { useState } from 'react';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';
import { motion } from 'framer-motion';
import { Clock, Ship, Waves, AlertTriangle, ShieldCheck, ArrowRight, Compass, Navigation } from 'lucide-react';
import { RippleButton } from './RippleButton';
import { useAppStore } from '../../state/appStore';

export const InteractiveVoyageSimulator: React.FC = () => {
  const { setCurrentView, setScenario, setActiveAssessment } = useAppStore();
  const { t } = useLingui();
  const currentHour = new Date().getHours();
  const initialDep = Math.max(0, Math.min(20, currentHour));
  const initialRet = Math.min(23, initialDep + 6);
  
  const [beamWidth, setBeamWidth] = useState<number>(4.5);
  const [departureHour, setDepartureHour] = useState<number>(initialDep);
  const [returnHour, setReturnHour] = useState<number>(initialRet);
  const [vesselType, setVesselType] = useState<string>(t`Mechanized Trawler (4.5m)`);

  const [waveForecast, setWaveForecast] = useState<number[] | null>(null);
  const [isFetchingWave, setIsFetchingWave] = useState(true);

  React.useEffect(() => {
    // Fetch live wave data for Mangalore coast for today from Open-Meteo Marine API
    setIsFetchingWave(true);
    fetch('https://marine-api.open-meteo.com/v1/marine?latitude=12.87&longitude=74.84&hourly=wave_height&timezone=Asia%2FKolkata&forecast_days=1')
      .then(res => res.json())
      .then(data => {
        if (data && data.hourly && data.hourly.wave_height) {
          setWaveForecast(data.hourly.wave_height);
        }
      })
      .catch(err => console.error("Failed to fetch live wave data for simulator", err))
      .finally(() => setIsFetchingWave(false));
  }, []);

  // Deterministic SVAS Limit: beam / 4.0
  const svasLimit = beamWidth / 4.0;

  // Fallback Afternoon Swell Curve (05:00 = 0.8m, 12:00 = 1.2m, 16:00 = 2.1m, 18:00 = 2.4m)
  const getForecastWave = (hour: number) => {
    if (hour <= 8) return 0.8;
    if (hour <= 11) return 1.1;
    if (hour <= 13) return 1.3;
    if (hour <= 15) return 1.7;
    if (hour <= 17) return 2.1;
    return 2.3;
  };

  const getWave = (hour: number) => {
    return waveForecast && waveForecast[hour] != null ? waveForecast[hour] : getForecastWave(hour);
  };

  const returnWave = getWave(returnHour);
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
              <h3 className="text-base font-extrabold text-sagar-navy"><Trans>Interactive 4D Voyage Risk Simulator</Trans></h3>
              <span className="text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-800 border border-sky-200">
                <Trans>Live SVAS Engine</Trans>
              </span>
            </div>
            <p className="text-xs text-slate-500">
              <Trans>Test how boat physical beam width and return hour determine capsize risk in real time.</Trans>
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
              <span><Trans>SEVERE CAPSIZE HAZARD</Trans></span>
            </>
          ) : isCaution ? (
            <>
              <AlertTriangle className="w-4 h-4 text-amber-700 shrink-0" />
              <span><Trans>ELEVATED SWELL CAUTION</Trans></span>
            </>
          ) : (
            <>
              <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
              <span><Trans>CONDITIONS FAVORABLE</Trans></span>
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
            <span><Trans>1. Select Boat Hull Specification:</Trans></span>
          </label>
          <div className="grid grid-cols-3 gap-2">
            {[
              { label: t`FRP Boat`, beam: 2.2, desc: t`2.2m beam` },
              { label: t`Trawler`, beam: 4.5, desc: t`4.5m beam` },
              { label: t`Seiner`, beam: 6.0, desc: t`6.0m beam` },
            ].map((v) => (
              <button
                key={v.label}
                onClick={() => {
                  setBeamWidth(v.beam);
                  setVesselType(`${v.label} (${v.beam}m)`);
                }}
                className={`p-3 rounded-2xl border text-left transition-all touch-target ${
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
            <span className="text-slate-600 font-sans font-medium"><Trans>Deterministic SVAS Limit (Beam/4.0):</Trans></span>
            <strong className="text-sky-800 font-bold text-sm"><Trans>{svasLimit.toFixed(2)} meters</Trans></strong>
          </div>
        </div>

        {/* Right: Return Time Slider */}
        <div className="space-y-4">
          
          {/* Departure Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-sky-600" />
                <span><Trans>2. Departure Time:</Trans></span>
              </label>
              <span className="text-xs font-mono font-extrabold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200">
                <Trans>{departureHour}:00 IST</Trans>
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="23"
              step="1"
              value={departureHour}
              onChange={(e) => {
                const dep = parseInt(e.target.value);
                setDepartureHour(dep);
                if (dep >= returnHour) setReturnHour(Math.min(23, dep + 1));
              }}
              className="w-full accent-sky-600 cursor-pointer h-2 bg-sagar-canvasAlt rounded-lg"
            />
          </div>

          {/* Return Slider */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-xs font-bold text-slate-700 uppercase tracking-wider flex items-center gap-1.5">
                <Clock className="w-4 h-4 text-sky-600" />
                <span><Trans>3. Expected Return:</Trans></span>
              </label>
              <span className="text-xs font-mono font-extrabold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-900 border border-sky-200">
                <Trans>{returnHour}:00 IST</Trans>
              </span>
            </div>
            <input
              type="range"
              min={departureHour + 1}
              max="23"
              step="1"
              value={returnHour}
              onChange={(e) => setReturnHour(parseInt(e.target.value))}
              className="w-full accent-rose-600 cursor-pointer h-2 bg-sagar-canvasAlt rounded-lg"
            />
            
            <div className="flex justify-between text-[11px] text-slate-500 font-mono mt-2">
              <span>06:00 ({getWave(6).toFixed(1)}m)</span>
              <span>12:00 ({getWave(12).toFixed(1)}m)</span>
              <span className="text-rose-700 font-bold">18:00 ({getWave(18).toFixed(1)}m)</span>
            </div>
          </div>

          <div className="p-3 bg-sagar-canvasAlt rounded-xl border border-sagar-borderLight flex items-center justify-between text-xs font-mono">
            <span className="text-slate-600 font-sans font-medium">
              {isFetchingWave ? <Trans>Fetching Live Wave Forecast...</Trans> : <Trans>Forecasted Sea Wave at {returnHour}:00:</Trans>}
            </span>
            <strong className={`font-bold text-sm ${isSevere ? 'text-rose-700' : 'text-sagar-navy'}`}>
              <Trans>{returnWave.toFixed(1)} meters</Trans>
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
              ? <Trans>Critical 4D Spatio-Temporal Hazard Explanation</Trans>
              : isCaution
              ? <Trans>Marginal Safety Clearance Warning</Trans>
              : <Trans>Safe Navigation Profile</Trans>}
          </div>
          <p className="text-xs leading-relaxed text-slate-800 font-medium">
            {isSevere ? (
              <Trans>
                For your <strong>{vesselType}</strong>, the safe capsize limit is{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong>. By{' '}
                <strong>{returnHour}:00 IST</strong>, forecasted coastal wave height climbs to{' '}
                <strong className="font-mono text-rose-700">{returnWave.toFixed(1)} m</strong>. Leaving early or returning before 12:00 PM prevents capsizing risks.
              </Trans>
            ) : isCaution ? (
              <Trans>
                Wave heights at <strong>{returnHour}:00 IST ({returnWave.toFixed(1)} m)</strong> are close to your boat limit of{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong>. Exercise caution during return approach.
              </Trans>
            ) : (
              <Trans>
                Wave heights during <strong>{returnHour}:00 IST ({returnWave.toFixed(1)} m)</strong> remain comfortably under your vessel's safe limit of{' '}
                <strong className="font-mono">{svasLimit.toFixed(2)} m</strong>.
              </Trans>
            )}
          </p>
        </div>
      </motion.div>

      {/* Action Footer */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 pt-1">
        <span className="text-xs text-slate-500 font-medium text-center sm:text-left">
          <Trans>Ready to assess your real voyage coordinates and 4D trajectory?</Trans>
        </span>
        <RippleButton
          variant="primary"
          size="md"
          icon={<Navigation className="w-4 h-4" />}
          iconRight={<ArrowRight className="w-4 h-4" />}
          onClick={() => setCurrentView('chat')}
        >
          <Trans>Plan My Maritime Voyage</Trans>
        </RippleButton>
      </div>
    </div>
  );
};
