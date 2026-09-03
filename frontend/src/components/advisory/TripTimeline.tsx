import React from 'react';
import { Trajectory, Waypoint } from '../../types/trip';
import { HazardFlag } from '../../types/risk';
import { useAppStore } from '../../state/appStore';
import { Clock, MapPin, AlertTriangle, ShieldCheck, Navigation, ArrowRight, Waves } from 'lucide-react';
import { motion } from 'framer-motion';
import { Trans, useLingui } from '@lingui/react/macro';

interface Props {
  trajectory: Trajectory;
  hazardFlags?: HazardFlag[];
}

export const TripTimeline: React.FC<Props> = ({ trajectory, hazardFlags = [] }) => {
  const { t } = useLingui();
  const { selectedWaypointIndex, setSelectedWaypointIndex } = useAppStore();

  const getWaypointRisk = (index: number, phase: string) => {
    const hazard = hazardFlags.find((h) => h.waypoint_index === index || (h.trip_phase === phase && phase === 'RETURN'));
    if (hazard) {
      const isSevere = hazard.observed_value >= hazard.threshold_value * 1.3;
      return isSevere
        ? {
            dotClass: 'bg-rose-600 text-white ring-4 ring-rose-100',
            badgeClass: 'bg-rose-50 text-rose-800 border-rose-200',
            badge: t`SEVERE HAZARD`,
            label: t`Wave ${hazard.observed_value}m > ${hazard.threshold_value}m limit`,
            isSevere: true,
          }
        : {
            dotClass: 'bg-amber-500 text-white ring-4 ring-amber-100',
            badgeClass: 'bg-amber-50 text-amber-800 border-amber-200',
            badge: t`MODERATE RISK`,
            label: t`Elevated wave swell`,
            isSevere: false,
          };
    }
    return {
      dotClass: 'bg-emerald-600 text-white ring-4 ring-emerald-100',
      badgeClass: 'bg-emerald-50 text-emerald-800 border-emerald-200',
      badge: t`SAFE`,
      label: t`Conditions within limits`,
      isSevere: false,
    };
  };

  const getPhasePill = (phase: string) => {
    switch (phase) {
      case 'DEPARTURE':
        return 'bg-sky-100 text-sky-800 border-sky-200';
      case 'OUTBOUND':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'FISHING':
        return 'bg-teal-100 text-teal-800 border-teal-200';
      case 'RETURN':
        return 'bg-indigo-100 text-indigo-800 border-indigo-200';
      case 'ARRIVAL':
        return 'bg-emerald-100 text-emerald-800 border-emerald-200';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-200';
    }
  };

  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3.5">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
            <Clock className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-sagar-navy">
              <Trans>4D Voyage Journey Timeline</Trans>
            </h3>
            <p className="text-[11px] text-sagar-textMuted"><Trans>Click waypoints to focus map camera & ETA conditions</Trans></p>
          </div>
        </div>
        <span className="text-xs font-mono font-bold px-2.5 py-1 rounded-lg bg-sagar-canvasAlt text-slate-700 border border-sagar-border">
          <Trans>{trajectory.total_distance_km} km voyage</Trans>
        </span>
      </div>

      {/* Connected Journey Path */}
      <div className="relative pl-7 space-y-4 before:absolute before:left-3.5 before:top-3 before:bottom-3 before:w-0.5 before:bg-gradient-to-b before:from-sky-400 before:via-teal-400 before:to-indigo-500">
        {trajectory.waypoints.map((wp, idx) => {
          const risk = getWaypointRisk(idx, wp.phase);
          const isSelected = selectedWaypointIndex === idx;

          return (
            <motion.div
              key={idx}
              onClick={() => setSelectedWaypointIndex(idx)}
              className={`relative cursor-pointer transition-all p-4 rounded-xl border touch-target ${
                isSelected
                  ? 'bg-sagar-powder/60 border-sky-400 shadow-soft-md ring-2 ring-sky-300'
                  : risk.isSevere
                  ? 'bg-rose-50/40 border-rose-200 hover:border-rose-300'
                  : 'bg-white border-sagar-borderLight hover:bg-sagar-canvasAlt/80 hover:border-sagar-border'
              }`}
              whileHover={{ x: 2 }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedWaypointIndex(idx)}
              aria-label={`Select waypoint ${idx + 1}: ${wp.name || wp.phase}`}
            >
              {/* Step Dot Node */}
              <div
                className={`absolute -left-[27px] top-4 w-6 h-6 rounded-full flex items-center justify-center font-extrabold text-[10px] shadow-soft-sm transition-transform ${
                  risk.dotClass
                } ${isSelected ? 'scale-125' : ''}`}
              >
                {idx + 1}
              </div>

              {/* Waypoint Card Header: Time & Phase */}
              <div className="flex flex-wrap items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-extrabold text-sagar-navy font-mono">
                    {new Date(wp.eta_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST
                  </span>
                  <span className={`text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border ${getPhasePill(wp.phase)}`}>
                    {wp.phase}
                  </span>
                </div>

                <span className={`text-[10px] font-extrabold uppercase px-2 py-0.5 rounded border ${risk.badgeClass}`}>
                  {risk.badge}
                </span>
              </div>

              {/* Waypoint Name & Position */}
              <div className="flex items-center gap-1.5 text-xs text-sagar-navy font-bold">
                <MapPin className="w-3.5 h-3.5 text-sky-600 shrink-0" />
                <span>{wp.name || t`Waypoint ${idx + 1}`}</span>
              </div>

              {/* Details & Wave Status */}
              <div className="flex items-center justify-between text-[11px] text-sagar-textMuted mt-1.5 pt-1.5 border-t border-sagar-borderLight">
                <span className="font-mono">{wp.lat.toFixed(2)}°N, {wp.lon.toFixed(2)}°E</span>
                <span className={`font-semibold ${risk.isSevere ? 'text-rose-700 font-bold' : 'text-slate-600'}`}>
                  {risk.label}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
