import React from 'react';
import { MarineObservation } from '../../types/api';
import { Thermometer, Activity, ShieldAlert, Fish, Compass } from 'lucide-react';

interface Props {
  observations?: MarineObservation[];
  pfzAvailable?: boolean;
}

export const MarineCard: React.FC<Props> = ({ observations, pfzAvailable = true }) => {
  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2">
          <Fish className="w-4 h-4 text-sky-600" />
          <h3 className="text-xs font-bold text-sagar-navy uppercase tracking-wider">
            Oceanographic & PFZ Satellite Signals
          </h3>
        </div>
        <span
          className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
            pfzAvailable
              ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
              : 'bg-amber-100 text-amber-800 border-amber-300'
          }`}
        >
          {pfzAvailable ? 'PFZ SIGNALS ACTIVE' : 'PFZ CLOUD OBSTRUCTED'}
        </span>
      </div>

      {!observations || observations.length === 0 ? (
        <p className="text-xs text-slate-500">
          No oceanographic satellite observations available for this trajectory.
        </p>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
          {observations.map((obs, idx) => (
            <div key={idx} className="bg-sagar-canvasAlt p-4 rounded-xl border border-sagar-borderLight space-y-2 text-xs">
              <div className="flex justify-between items-center border-b border-sagar-borderLight pb-2">
                <span className="font-bold text-sagar-navy font-mono">
                  Zone ({obs.lat.toFixed(2)}°N, {obs.lon.toFixed(2)}°E)
                </span>
                <span className="text-[10px] text-slate-500 font-mono">
                  {new Date(obs.time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST
                </span>
              </div>

              <div className="space-y-1.5 pt-1">
                <div className="flex justify-between items-center font-mono">
                  <span className="text-slate-500 font-sans flex items-center gap-1.5">
                    <Thermometer className="w-3.5 h-3.5 text-sky-600" /> Sea Surface Temp:
                  </span>
                  <strong className="text-sky-800 font-bold">{obs.sst_celsius} °C</strong>
                </div>

                <div className="flex justify-between items-center font-mono">
                  <span className="text-slate-500 font-sans flex items-center gap-1.5">
                    <Activity className="w-3.5 h-3.5 text-emerald-600" /> Chlorophyll-a:
                  </span>
                  <strong className="text-emerald-700 font-bold">{obs.chlorophyll_mgm3} mg/m³</strong>
                </div>

                <div className="flex justify-between items-center font-mono">
                  <span className="text-slate-500 font-sans flex items-center gap-1.5">
                    <ShieldAlert className="w-3.5 h-3.5 text-amber-600" /> HAB Risk:
                  </span>
                  <strong className={obs.hab_detected ? 'text-rose-700 font-bold' : 'text-slate-700'}>
                    {(obs.hab_probability * 100).toFixed(0)}% {obs.hab_detected ? '(HAB DETECTED)' : '(Low)'}
                  </strong>
                </div>

                <div className="flex justify-between items-center font-mono">
                  <span className="text-slate-500 font-sans flex items-center gap-1.5">
                    <Compass className="w-3.5 h-3.5 text-sky-600" /> Surface Currents:
                  </span>
                  <strong className="text-slate-700">{obs.current_speed_kmh} km/h</strong>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
