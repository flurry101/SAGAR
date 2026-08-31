import React from 'react';
import { Shield } from 'lucide-react';
import { formatSagarDisclaimer } from '../../utils/brand';

interface Props {
  text?: string;
}

export const DisclaimerFooter: React.FC<Props> = ({ text }) => {
  return (
    <footer className="mt-8 p-4 sm:p-5 bg-white border border-sagar-border rounded-2xl text-xs text-slate-600 max-w-4xl mx-auto space-y-2 shadow-soft-sm">
      <div className="flex items-center gap-2 font-bold text-sagar-navy">
        <Shield className="w-4 h-4 text-sky-600 shrink-0" />
        <span>Operational Decision-Support Disclaimer</span>
      </div>
      <p className="leading-relaxed text-[11px] text-slate-500 font-normal">
        {formatSagarDisclaimer(text)}
      </p>
    </footer>
  );
};
