import React from 'react';
import { WeatherObservation } from '../../types/api';
import { Waves, Wind, Eye, Compass, Clock, AlertTriangle } from 'lucide-react';

interface Props {
  forecasts?: WeatherObservation[];
}

export const WeatherCard: React.FC<Props> = ({ forecasts }) => {
  if (!forecasts || forecasts.length === 0) return null;

  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2">
          <Waves className="w-4 h-4 text-sky-600" />
          <h3 className="text-xs font-bold text-sagar-navy uppercase tracking-wider">
            Weather & Sea State Forecast (Time-Aligned)
          </h3>
        </div>
        <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-sagar-powder text-sky-800 border border-sky-200 font-mono font-semibold">
          Waypoint Interpolated
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3.5">
        {forecasts.map((fc, idx) => (
          <div key={idx} className="bg-sagar-canvasAlt p-4 rounded-xl border border-sagar-borderLight space-y-2.5 text-xs">
            <div className="flex items-center justify-between border-b border-sagar-borderLight pb-2">
              <span className="font-bold text-sagar-navy flex items-center gap-1.5 font-mono">
                <Clock className="w-3.5 h-3.5 text-sky-600" />
                {new Date(fc.time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST
              </span>
              {fc.stale ? (
                <span className="text-[9px] font-extrabold px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-800 border border-amber-300 flex items-center gap-1">
                  <AlertTriangle className="w-2.5 h-2.5 text-amber-700" />
                  STALE
                </span>
              ) : (
                <span className="text-[9px] font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
                  Live Model
                </span>
              )}
            </div>

            <div className="space-y-2 pt-1">
              <div className="flex justify-between items-center">
                <span className="text-slate-500 flex items-center gap-1.5">
                  <Waves className="w-3.5 h-3.5 text-sky-600" /> Wave Height:
                </span>
                <strong className={`text-sm font-mono ${fc.wave_height_m >= 2.0 ? 'text-rose-700 font-extrabold' : 'text-sagar-navy'}`}>
                  {fc.wave_height_m} m
                </strong>
              </div>

              <div className="flex justify-between items-center font-mono">
                <span className="text-slate-500 font-sans flex items-center gap-1.5">
                  <Wind className="w-3.5 h-3.5 text-sky-600" /> Wind Speed:
                </span>
                <strong className="text-slate-800">{fc.wind_speed_kmh} km/h</strong>
              </div>

              <div className="flex justify-between items-center font-mono">
                <span className="text-slate-500 font-sans flex items-center gap-1.5">
                  <Compass className="w-3.5 h-3.5 text-sky-600" /> Swell:
                </span>
                <strong className="text-slate-800">{fc.swell_height_m} m</strong>
              </div>

              <div className="flex justify-between items-center font-mono">
                <span className="text-slate-500 font-sans flex items-center gap-1.5">
                  <Eye className="w-3.5 h-3.5 text-sky-600" /> Visibility:
                </span>
                <strong className="text-slate-800">{fc.visibility_km} km</strong>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
