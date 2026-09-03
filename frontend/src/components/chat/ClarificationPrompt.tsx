import React, { useState } from 'react';
import { HelpCircle, Send } from 'lucide-react';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

interface Props {
  onProvideInfo: (infoText: string) => void;
  missingFields?: any[];
}

export const ClarificationPrompt: React.FC<Props> = ({ onProvideInfo, missingFields = [] }) => {
  const { t } = useLingui();
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [fallbackInput, setFallbackInput] = useState('');

  const isMulti = missingFields && missingFields.length > 0;

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (isMulti) {
      // combine answers into a sentence so the LLM understands it easily
      const combined = missingFields
        .map(f => `${f.field.replace(/_/g, ' ')} is ${answers[f.field] || 'unknown'}`)
        .join('. ');
      onProvideInfo(combined);
    } else {
      if (!fallbackInput.trim()) return;
      onProvideInfo(fallbackInput.trim());
      setFallbackInput('');
    }
  };

  const isSubmitDisabled = isMulti 
    ? missingFields.some(f => !answers[f.field]?.trim()) 
    : !fallbackInput.trim();

  return (
    <div className="my-4 p-5 bg-amber-50 border border-amber-300 rounded-2xl shadow-soft-sm">
      <div className="flex items-center gap-2 text-amber-900 font-bold text-sm mb-2">
        <HelpCircle className="w-5 h-5 text-amber-700 shrink-0" />
        <span><Trans>Voyage Clarification Required</Trans></span>
      </div>
      <p className="text-xs sm:text-sm text-slate-700 mb-3">
        <Trans>SAGAR never guesses safety-critical voyage or boat parameters. Please provide the missing details below:</Trans>
      </p>

      <form onSubmit={handleSubmit} className="space-y-3">
        {isMulti ? (
          <div className="space-y-3 bg-white p-4 rounded-xl border border-amber-200 shadow-soft-sm">
            {missingFields.map((f, idx) => (
              <div key={idx} className="flex flex-col gap-1.5">
                <label className="text-xs font-bold text-amber-900 capitalize flex items-center gap-1.5">
                  <span className="text-amber-600 font-bold">•</span>
                  {f.field.replace(/_/g, ' ')} <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={answers[f.field] || ''}
                  onChange={(e) => setAnswers(prev => ({ ...prev, [f.field]: e.target.value }))}
                  placeholder={`Enter ${f.field.replace(/_/g, ' ')}...`}
                  className="w-full bg-slate-50 border border-sagar-border focus:border-sky-500 rounded-lg px-3 py-2 text-sm text-sagar-navy placeholder-slate-400 focus:outline-none"
                />
              </div>
            ))}
          </div>
        ) : (
          <input
            type="text"
            value={fallbackInput}
            onChange={(e) => setFallbackInput(e.target.value)}
            placeholder={t`e.g. Departure 5:00 AM, Mechanized Trawler with 4.5m beam width...`}
            className="w-full bg-white border border-sagar-border focus:border-sky-500 rounded-xl px-3.5 py-2.5 text-xs sm:text-sm text-sagar-navy placeholder-slate-400 focus:outline-none shadow-soft-sm"
          />
        )}

        <div className="flex justify-end pt-2">
          <button
            type="submit"
            disabled={isSubmitDisabled}
            className="bg-amber-600 hover:bg-amber-500 text-white font-bold px-5 py-2.5 rounded-xl text-sm flex items-center gap-2 disabled:opacity-50 transition-all shadow-soft-sm touch-target"
          >
            <span><Trans>Submit Details</Trans></span>
            <Send className="w-4 h-4" />
          </button>
        </div>
      </form>
    </div>
  );
};
