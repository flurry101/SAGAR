import React, { useState } from 'react';
import { useAppStore } from '../../state/appStore';
import { vesselApi } from '../../api/vesselApi';
import { Ship, Ruler, Gauge, Save, ShieldCheck, Anchor } from 'lucide-react';
import { motion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

export const VesselForm: React.FC = () => {
  const { t } = useLingui();
  const { userVessel, setUserVessel } = useAppStore();

  const [vesselType, setVesselType] = useState(userVessel?.vessel_type || 'Mechanized Trawler');
  const [beamWidth, setBeamWidth] = useState(userVessel?.beam_width_m || 4.5);
  const [length, setLength] = useState(userVessel?.length_m || 14.5);
  const [speed, setSpeed] = useState(userVessel?.cruising_speed_kmh || 15.0);
  const [registration, setRegistration] = useState(userVessel?.registration_number || 'IND-KA-04-MM-8821');
  const [homePort, setHomePort] = useState(userVessel?.home_port || 'Mangalore Old Port');
  const [hasAis, setHasAis] = useState(userVessel?.has_ais !== false);
  const [saved, setSaved] = useState(false);

  // Deterministic SVAS Formula (Beam Width / 4.0)
  const maxSafeWave = (parseFloat(beamWidth as any) || 4.5) / 4.0;

  const handlePresetSelect = (preset: { type: string; beam: number; len: number; spd: number }) => {
    setVesselType(preset.type);
    setBeamWidth(preset.beam);
    setLength(preset.len);
    setSpeed(preset.spd);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    const updated = {
      vessel_id: userVessel?.vessel_id || 'vessel-001',
      vessel_type: vesselType,
      beam_width_m: parseFloat(beamWidth as any),
      length_m: parseFloat(length as any),
      cruising_speed_kmh: parseFloat(speed as any),
      registration_number: registration,
      home_port: homePort,
      has_ais: hasAis,
      safety_thresholds: {
        max_safe_wave_m: maxSafeWave,
        rule_applied: 'SVAS_CAPSIZE_BSI',
        formula: 'beam_width_m / 4.0'
      }
    };

    setUserVessel(updated);
    try {
      await vesselApi.updateVesselProfile(updated.vessel_id, updated);
    } catch (err) {
      console.warn('Vessel profile saved locally in store:', err);
    }
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white border border-sagar-border rounded-2xl p-6 sm:p-8 shadow-soft-sm space-y-6 max-w-2xl mx-auto my-4 text-sagar-navy">
      <div className="flex items-center gap-3 border-b border-sagar-borderLight pb-4">
        <div className="w-11 h-11 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
          <Ship className="w-6 h-6" />
        </div>
        <div>
          <h2 className="text-base sm:text-lg font-bold text-sagar-navy"><Trans>Vessel Specification Profile</Trans></h2>
          <p className="text-xs text-slate-500">
            <Trans>Physical boat dimensions determine deterministic SVAS capsize wave safety limits.</Trans>
          </p>
        </div>
      </div>

      {saved && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs flex items-center gap-2 font-medium">
          <ShieldCheck className="w-4 h-4 text-emerald-700 shrink-0" />
          <span><Trans>Vessel profile updated & SVAS max safe wave limit recalculated!</Trans></span>
        </div>
      )}

      {/* Quick Indian Coastal Presets */}
      <div className="space-y-2">
        <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
          <Trans>Standard Coastal Boat Presets:</Trans>
        </span>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          {[
            { label: t`Mechanized Trawler`, type: 'Mechanized Trawler', beam: 4.5, len: 14.5, spd: 15.0 },
            { label: t`Motorized FRP Boat`, type: 'Motorized Fibre Craft', beam: 2.2, len: 8.5, spd: 18.0 },
            { label: t`Deep Sea Seiner`, type: 'Deep Sea Purse Seiner', beam: 6.0, len: 24.0, spd: 16.0 },
            { label: t`Traditional Catamaran`, type: 'Traditional Non-Motorized Catamaran', beam: 1.8, len: 6.0, spd: 8.0 },
          ].map((preset, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => handlePresetSelect(preset)}
              className="p-3 rounded-xl bg-sagar-canvasAlt hover:bg-sagar-powder border border-sagar-borderLight text-sagar-navy text-left transition-colors touch-target"
            >
              <div className="font-bold text-[11px] text-sky-900 truncate">{preset.label}</div>
              <div className="text-[10px] text-slate-500 font-mono font-medium">{preset.beam}m beam</div>
            </button>
          ))}
        </div>
      </div>

      {/* Computed Limit Live Badge */}
      <div className="p-4 bg-sagar-canvasAlt border border-sagar-borderLight rounded-xl flex items-center justify-between text-xs">
        <div>
          <span className="text-slate-500 font-medium block"><Trans>Computed SVAS Max Wave Limit:</Trans></span>
          <span className="text-xl font-extrabold text-sagar-navy font-mono">{maxSafeWave.toFixed(3)} <Trans>meters</Trans></span>
        </div>
        <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-1 rounded-full bg-sagar-powder text-sky-800 border border-sky-200 font-mono">
          <Trans>Formula:</Trans> Beam / 4.0
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Vessel Type</Trans></label>
          <input
            type="text"
            value={vesselType}
            onChange={(e) => setVesselType(e.target.value)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Beam Width (meters)</Trans></label>
          <input
            type="number"
            step="0.1"
            value={beamWidth}
            onChange={(e) => setBeamWidth(e.target.value as any)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none font-bold text-sky-800 font-mono"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Overall Length (meters)</Trans></label>
          <input
            type="number"
            step="0.1"
            value={length}
            onChange={(e) => setLength(e.target.value as any)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none font-mono"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Cruising Speed (km/h)</Trans></label>
          <input
            type="number"
            step="0.5"
            value={speed}
            onChange={(e) => setSpeed(e.target.value as any)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none font-mono"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Registration Number</Trans></label>
          <input
            type="text"
            value={registration}
            onChange={(e) => setRegistration(e.target.value)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
          />
        </div>

        <div>
          <label className="text-xs font-semibold text-slate-700 block mb-1"><Trans>Base Port / Harbor</Trans></label>
          <input
            type="text"
            value={homePort}
            onChange={(e) => setHomePort(e.target.value)}
            className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2 text-xs sm:text-sm text-sagar-navy focus:border-sky-500 focus:outline-none"
          />
        </div>
      </div>

      <div className="flex items-center gap-3 pt-1">
        <input
          type="checkbox"
          id="hasAis"
          checked={hasAis}
          onChange={(e) => setHasAis(e.target.checked)}
          className="w-4 h-4 rounded bg-white border-sagar-border text-sky-600 focus:ring-sky-500"
        />
        <label htmlFor="hasAis" className="text-xs text-slate-700 cursor-pointer font-medium">
          <Trans>Equipped with active AIS Transponder / VMS Beacon</Trans>
        </label>
      </div>

      <button
        type="submit"
        className="w-full py-3.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs sm:text-sm shadow-soft-sm flex items-center justify-center gap-2 transition-all touch-target"
      >
        <Save className="w-4 h-4" />
        <span><Trans>Save Vessel Profile</Trans></span>
      </button>
    </form>
  );
};
