import React, { useState } from 'react';
import { HelpCircle, Send } from 'lucide-react';
import { Trans, useLingui } from '@lingui/react/macro';

interface Props {
  onProvideInfo: (infoText: string) => void;
  missingFields?: any[];
}

export const ClarificationPrompt: React.FC<Props> = ({ onProvideInfo, missingFields }) => {
  const { t } = useLingui();
  const [responseInput, setResponseInput] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!responseInput.trim()) return;
    onProvideInfo(responseInput.trim());
    setResponseInput('');
  };

  return (
    <div className="my-4 p-5 bg-amber-50 border border-amber-300 rounded-2xl shadow-soft-sm">
      <div className="flex items-center gap-2 text-amber-900 font-bold text-sm mb-2">
        <HelpCircle className="w-5 h-5 text-amber-700 shrink-0" />
        <span><Trans>Voyage Clarification Required</Trans></span>
      </div>
      <p className="text-xs sm:text-sm text-slate-700 mb-3">
        <Trans>SAGAR never guesses safety-critical voyage or boat parameters. Please provide the missing details below:</Trans>
      </p>

      {missingFields && missingFields.length > 0 && (
        <div className="space-y-1.5 mb-3 bg-white p-3.5 rounded-xl border border-amber-200 shadow-soft-sm">
          {missingFields.map((field, idx) => (
            <div key={idx} className="text-xs text-amber-950 flex items-start gap-2 font-medium">
              <span className="text-amber-600 font-bold">•</span>
              <span>{field.question || `${field.field}: ${field.reason || 'Required for safety calculation'}`}</span>
            </div>
          ))}
        </div>
      )}

      <form onSubmit={handleSubmit} className="flex gap-2">
        <input
          type="text"
          value={responseInput}
          onChange={(e) => setResponseInput(e.target.value)}
          placeholder={t`e.g. Departure 5:00 AM, Mechanized Trawler with 4.5m beam width...`}
          className="flex-1 bg-white border border-sagar-border focus:border-sky-500 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-sagar-navy placeholder-slate-400 focus:outline-none shadow-soft-sm"
        />
        <button
          type="submit"
          disabled={!responseInput.trim()}
          className="bg-amber-600 hover:bg-amber-500 text-white font-bold px-4 py-2.5 rounded-xl text-xs sm:text-sm flex items-center gap-1.5 disabled:opacity-50 transition-all shadow-soft-sm shrink-0 touch-target"
        >
          <span><Trans>Submit</Trans></span>
          <Send className="w-3.5 h-3.5" />
        </button>
      </form>
    </div>
  );
};
