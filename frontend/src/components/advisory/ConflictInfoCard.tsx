import React from 'react';
import { DataConflict } from '../../types/risk';
import { AlertCircle } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';
import { Trans } from '@lingui/react/macro';

interface Props {
  conflicts: DataConflict[];
}

export const ConflictInfoCard: React.FC<Props> = ({ conflicts }) => {
  if (!conflicts || conflicts.length === 0) return null;

  return (
    <div className="bg-amber-50 border border-amber-300 rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center gap-2.5 text-amber-950 font-bold text-sm border-b border-amber-200 pb-3">
        <AlertCircle className="w-5 h-5 text-amber-700 shrink-0" />
        <span><Trans>Conflicting Data Sources Detected (Multi-Source Comparison)</Trans></span>
      </div>

      <p className="text-xs text-slate-700 leading-relaxed font-medium">
        <Trans>Different authoritative weather/marine models report divergent values for your voyage window. SAGAR presents both sources transparently without fabricating an ungrounded consensus:</Trans>
      </p>

      {conflicts.map((conf, idx) => (
        <div key={idx} className="bg-white p-4 rounded-xl border border-amber-200 space-y-3 shadow-soft-sm">
          <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
            <span><Trans>Parameter:</Trans> {conf.variable}</span>
            <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-900 border border-amber-300 uppercase font-extrabold">
              {conf.conflict_indicator}
            </span>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
            {/* Source A */}
            <div className="p-3 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">
                <Trans>Source A:</Trans> {conf.source_a.name}
              </span>
              <span className="text-sm font-bold text-rose-700 block font-mono">{conf.source_a.value}</span>
              <span className="text-[10px] text-slate-500 block mt-1 font-mono">
                <Trans>Timestamp:</Trans> {conf.source_a.timestamp}
              </span>
            </div>

            {/* Source B */}
            <div className="p-3 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight">
              <span className="text-[10px] text-slate-500 uppercase font-bold block mb-1">
                <Trans>Source B:</Trans> {conf.source_b.name}
              </span>
              <span className="text-sm font-bold text-emerald-700 block font-mono">{conf.source_b.value}</span>
              <span className="text-[10px] text-slate-500 block mt-1 font-mono">
                <Trans>Timestamp:</Trans> {conf.source_b.timestamp}
              </span>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};
