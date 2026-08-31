import React from 'react';
import { HazardFlag } from '../../types/risk';
import { ShieldAlert, Clock, Database, Ruler } from 'lucide-react';

interface Props {
  hazard: HazardFlag;
}

export const HazardAlert: React.FC<Props> = ({ hazard }) => {
  const isSevere = hazard.observed_value >= hazard.threshold_value * 1.3;

  return (
    <div
      className={`p-4 sm:p-5 rounded-2xl border shadow-soft-sm space-y-3.5 ${
        isSevere
          ? 'bg-rose-50 border-rose-200 text-rose-950'
          : 'bg-amber-50 border-amber-200 text-amber-950'
      }`}
    >
      <div className="flex items-center justify-between border-b border-rose-200/60 pb-2.5">
        <div className="flex items-center gap-2">
          <ShieldAlert className={`w-5 h-5 ${isSevere ? 'text-rose-700' : 'text-amber-700'}`} />
          <span className="font-extrabold text-xs sm:text-sm uppercase tracking-wide">
            {hazard.hazard_type.replace(/_/g, ' ')}
          </span>
        </div>
        <span className="text-[10px] font-bold uppercase px-2.5 py-0.5 rounded-full bg-white border border-rose-200 text-slate-700 shadow-soft-sm">
          Leg: {hazard.trip_phase}
        </span>
      </div>

      {/* Value Comparison */}
      <div className="grid grid-cols-2 gap-3 bg-white p-3.5 rounded-xl border border-rose-200/80 text-xs shadow-soft-sm">
        <div>
          <span className="text-slate-500 text-[10px] block uppercase font-bold">Observed Forecast</span>
          <span className={`text-base font-extrabold font-mono ${isSevere ? 'text-rose-700' : 'text-amber-700'}`}>
            {hazard.observed_value} {hazard.unit || ''}
          </span>
        </div>
        <div>
          <span className="text-slate-500 text-[10px] block uppercase font-bold">Boat Safety Limit</span>
          <span className="text-base font-extrabold text-sagar-navy font-mono">
            {hazard.threshold_value} {hazard.unit || ''}
          </span>
        </div>
      </div>

      {/* Applied Formula & Location */}
      <div className="space-y-1.5 text-xs text-slate-700">
        <div className="flex items-center gap-2">
          <Ruler className="w-3.5 h-3.5 text-sky-700 shrink-0" />
          <span>Rule Applied: <strong className="text-sagar-navy font-mono">{hazard.rule_applied}</strong></span>
        </div>
        <div className="flex items-center gap-2">
          <Clock className="w-3.5 h-3.5 text-sky-700 shrink-0" />
          <span>Hazard Time: <strong className="text-sagar-navy font-mono">{new Date(hazard.time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST</strong></span>
        </div>
      </div>

      {/* Provenance Badge */}
      {hazard.provenance && (
        <div className="pt-2.5 border-t border-rose-200/60 flex items-center justify-between text-[11px] text-slate-600">
          <div className="flex items-center gap-1.5">
            <Database className="w-3.5 h-3.5 text-slate-500" />
            <span className="truncate max-w-[180px] font-medium">{hazard.provenance.source}</span>
          </div>
          <span className="px-2.5 py-0.5 rounded-full text-[10px] font-extrabold bg-white text-sky-900 border border-sky-200 shadow-soft-sm">
            Tier {hazard.provenance.fallback_tier} • {hazard.provenance.confidence} CONFIDENCE
          </span>
        </div>
      )}
    </div>
  );
};
