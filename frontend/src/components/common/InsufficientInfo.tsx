import React from 'react';
import { InsufficientInfoData } from '../../types/api';
import { AlertOctagon, RefreshCw } from 'lucide-react';
import { useAppStore } from '../../state/appStore';
import { sanitizeSagarText, formatSagarDisclaimer } from '../../utils/brand';

interface Props {
  data?: InsufficientInfoData;
}

export const InsufficientInfo: React.FC<Props> = ({ data }) => {
  const { setCurrentView } = useAppStore();

  return (
    <div className="max-w-2xl mx-auto my-6 p-6 sm:p-8 bg-white border border-sagar-border rounded-2xl shadow-soft-md space-y-5 text-center text-sagar-navy">
      <div className="w-14 h-14 rounded-2xl bg-slate-100 border border-sagar-border flex items-center justify-center text-slate-600 mx-auto font-bold">
        <AlertOctagon className="w-7 h-7 text-slate-600" />
      </div>

      <div>
        <span className="text-xs font-bold px-3 py-1 rounded-full bg-sagar-canvasAlt text-slate-700 border border-sagar-border uppercase tracking-widest">
          INSUFFICIENT INFORMATION
        </span>
        <h2 className="text-lg sm:text-xl font-bold text-sagar-navy mt-3 mb-2">
          Unable to Safely Assess Your Voyage
        </h2>
        <p className="text-xs sm:text-sm text-slate-600 max-w-lg mx-auto leading-relaxed font-normal">
          {sanitizeSagarText(data?.recommendation_text) ||
            'SAGAR never fabricates or guesses safety-critical parameters. Assessment was paused because required vessel dimensions or temporal data is missing.'}
        </p>
      </div>

      {data?.missing_data && data.missing_data.length > 0 && (
        <div className="bg-sagar-canvasAlt p-4 rounded-xl border border-sagar-borderLight text-left max-w-md mx-auto space-y-2 text-xs">
          <span className="font-bold text-slate-600 block uppercase tracking-wider text-[10px]">
            Missing Safety Parameters:
          </span>
          <ul className="space-y-1.5">
            {data.missing_data.map((item, idx) => (
              <li key={idx} className="flex items-start gap-2 text-slate-800">
                <span className="text-amber-600 font-bold">•</span>
                <span>
                  <strong className="text-amber-800 uppercase">{item.data_type.replace(/_/g, ' ')}:</strong> {item.reason}
                </span>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="pt-2 flex justify-center gap-3">
        <button
          onClick={() => setCurrentView('chat')}
          className="px-6 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-soft-sm flex items-center gap-2 transition-all touch-target"
        >
          <RefreshCw className="w-4 h-4" />
          <span>Provide Missing Parameters in Planner</span>
        </button>
      </div>

      <p className="text-[11px] text-slate-500 max-w-md mx-auto pt-2">
        {formatSagarDisclaimer(data?.disclaimer)}
      </p>
    </div>
  );
};
