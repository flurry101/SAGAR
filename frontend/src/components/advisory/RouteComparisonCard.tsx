import React from 'react';
import { RouteCandidate } from '../../types/api';
import { useAppStore } from '../../state/appStore';
import { Navigation, Check, Award } from 'lucide-react';
import { motion } from 'framer-motion';

interface Props {
  routeCandidates?: RouteCandidate[];
}

export const RouteComparisonCard: React.FC<Props> = ({ routeCandidates = [] }) => {
  const { selectedRouteCandidateId, setSelectedRouteCandidateId } = useAppStore();

  if (!routeCandidates || routeCandidates.length === 0) return null;

  const activeId = selectedRouteCandidateId || routeCandidates[0]?.route_id;

  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2">
          <Navigation className="w-4 h-4 text-sky-600" />
          <h3 className="text-xs font-bold text-sagar-navy uppercase tracking-wider">
            Route Candidate Evaluation & Scoring
          </h3>
        </div>
        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-800 border border-sky-200">
          {routeCandidates.length} Scored Trajectories
        </span>
      </div>

      <p className="text-xs text-slate-600">
        SAGAR evaluates and scores candidate corridors against sea-state wave models, distance, and geofence boundaries:
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {routeCandidates.map((route) => {
          const isSelected = activeId === route.route_id;
          const isRecommended = route.is_recommended || route.score >= 85;

          return (
            <motion.div
              key={route.route_id}
              onClick={() => setSelectedRouteCandidateId(route.route_id)}
              className={`p-4 rounded-xl border cursor-pointer transition-all space-y-3 relative touch-target ${
                isSelected
                  ? 'bg-sagar-powder/40 border-sky-400 ring-2 ring-sky-300 shadow-soft-sm'
                  : 'bg-white border-sagar-borderLight hover:bg-sagar-canvasAlt/80 hover:border-sagar-border'
              }`}
              whileHover={{ y: -2 }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && setSelectedRouteCandidateId(route.route_id)}
            >
              {/* Header */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-sagar-navy">{route.name}</span>
                  {isRecommended && (
                    <span className="inline-flex items-center gap-1 text-[9px] font-extrabold uppercase px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                      <Award className="w-3 h-3 text-emerald-700" />
                      Recommended
                    </span>
                  )}
                </div>

                <div className="flex items-center gap-1.5">
                  <span className="text-xs font-extrabold text-sky-800 font-mono bg-sagar-powder px-2 py-0.5 rounded border border-sky-200">
                    {route.score.toFixed(1)}/100
                  </span>
                </div>
              </div>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 gap-2 text-xs">
                <div className="bg-sagar-canvasAlt p-2.5 rounded-lg border border-sagar-borderLight font-mono">
                  <span className="text-[10px] text-slate-500 block font-sans">Voyage Distance</span>
                  <span className="font-bold text-sagar-navy">{route.distance_nm} NM ({Math.round(route.distance_nm * 1.852)} km)</span>
                </div>
                <div className="bg-sagar-canvasAlt p-2.5 rounded-lg border border-sagar-borderLight font-mono">
                  <span className="text-[10px] text-slate-500 block font-sans">Est. Voyage Time</span>
                  <span className="font-bold text-sagar-navy">{route.duration_hours} Hours</span>
                </div>
              </div>

              {/* Penalty Breakdown */}
              {route.penalty_breakdown && (
                <div className="pt-2 border-t border-sagar-borderLight text-[11px] space-y-1">
                  <div className="flex justify-between text-slate-600">
                    <span>Weather Risk Penalty:</span>
                    <span className={route.penalty_breakdown.weather_risk > 0.2 ? 'text-rose-700 font-bold font-mono' : 'text-slate-800 font-mono'}>
                      {(route.penalty_breakdown.weather_risk * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="flex justify-between text-slate-600">
                    <span>Geofence Constraint:</span>
                    <span className={route.penalty_breakdown.geofence_penalty > 0 ? 'text-rose-700 font-bold' : 'text-emerald-700 font-bold'}>
                      {route.penalty_breakdown.geofence_penalty > 0 ? 'Boundary Violation' : 'Clear'}
                    </span>
                  </div>
                </div>
              )}

              {/* Selection Status */}
              <div className="flex items-center justify-between pt-1 text-[11px]">
                <span className="text-slate-500 capitalize">{route.route_type} Corridor</span>
                <span className={`font-bold flex items-center gap-1 ${isSelected ? 'text-sky-700' : 'text-slate-400'}`}>
                  {isSelected ? (
                    <>
                      <Check className="w-3.5 h-3.5 text-sky-700" />
                      <span>Active on Map</span>
                    </>
                  ) : (
                    <span>Click to Inspect</span>
                  )}
                </span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
