import React from 'react';
import { Advisory } from '../../types/advisory';
import { VesselProfile } from '../../types/vessel';
import { Ship, Clock, MapPin, Info } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';

interface Props {
  advisory: Advisory;
  vesselProfile?: VesselProfile;
}

export const AdvisoryCard: React.FC<Props> = ({ advisory, vesselProfile }) => {
  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <h3 className="text-xs font-bold text-sagar-navy uppercase tracking-wider flex items-center gap-2">
          <Info className="w-4 h-4 text-sky-600" />
          <span>Safety Reasoning & Context</span>
        </h3>
        {advisory.affected_phase && (
          <span className="text-[11px] font-bold px-2.5 py-0.5 rounded-full bg-rose-50 text-rose-800 border border-rose-200">
            Affected: {advisory.affected_phase}
          </span>
        )}
      </div>

      <div className="space-y-3 text-xs sm:text-sm">
        {advisory.reason && (
          <div>
            <span className="text-slate-500 font-semibold block mb-1 text-xs">Primary Safety Factor:</span>
            <p className="text-sagar-navy font-medium bg-sagar-canvasAlt p-3.5 rounded-xl border border-sagar-borderLight leading-relaxed">
              {sanitizeSagarText(advisory.reason)}
            </p>
          </div>
        )}

        {advisory.vessel_context && (
          <div className="flex items-start gap-2.5 bg-sagar-powder/50 border border-sky-200 p-3.5 rounded-xl text-sky-950">
            <Ship className="w-4 h-4 text-sky-700 shrink-0 mt-0.5" />
            <div>
              <span className="font-bold text-sky-900 block mb-0.5 text-xs">Vessel Stability Context:</span>
              <span className="text-xs text-sky-950">{sanitizeSagarText(advisory.vessel_context)}</span>
            </div>
          </div>
        )}

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
          {advisory.affected_time && (
            <div className="flex items-center gap-2.5 bg-sagar-canvasAlt p-3 rounded-xl border border-sagar-borderLight text-slate-700">
              <Clock className="w-4 h-4 text-sky-600 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Critical Time Window</span>
                <span className="font-bold text-xs text-sagar-navy font-mono">
                  {new Date(advisory.affected_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} IST
                </span>
              </div>
            </div>
          )}

          {advisory.affected_location && (
            <div className="flex items-center gap-2.5 bg-sagar-canvasAlt p-3 rounded-xl border border-sagar-borderLight text-slate-700">
              <MapPin className="w-4 h-4 text-sky-600 shrink-0" />
              <div>
                <span className="text-[10px] text-slate-500 block uppercase font-bold">Critical Zone</span>
                <span className="font-bold text-xs text-sagar-navy truncate block max-w-[190px]">
                  {advisory.affected_location}
                </span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
