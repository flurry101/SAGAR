import React from 'react';
import { RuleResult } from '../../types/risk';
import { ShieldCheck, CheckCircle2, XCircle } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';

interface Props {
  ruleResults?: RuleResult[];
}

export const RuleResultsPanel: React.FC<Props> = ({ ruleResults = [] }) => {
  if (!ruleResults || ruleResults.length === 0) return null;

  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2">
          <ShieldCheck className="w-4 h-4 text-sky-600" />
          <h3 className="text-xs font-bold text-sagar-navy uppercase tracking-wider">
            Deterministic Stability & Safety Rules
          </h3>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">
          {ruleResults.filter((r) => r.status === 'PASSED').length}/{ruleResults.length} Rules Passed
        </span>
      </div>

      <div className="space-y-2.5">
        {ruleResults.map((rule, idx) => {
          const isPassed = rule.status === 'PASSED';
          const isSevere = rule.risk_level === 'SEVERE';

          return (
            <div
              key={idx}
              className={`p-3.5 rounded-xl border transition-colors ${
                isPassed
                  ? 'bg-sagar-canvasAlt border-sagar-borderLight'
                  : isSevere
                  ? 'bg-rose-50 border-rose-200'
                  : 'bg-amber-50 border-amber-200'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1.5">
                <div className="flex items-center gap-2">
                  {isPassed ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                  ) : (
                    <XCircle className="w-4 h-4 text-rose-600 shrink-0" />
                  )}
                  <span className="text-xs font-bold text-sagar-navy">{rule.rule_name}</span>
                </div>

                <span
                  className={`text-[9px] font-black uppercase px-2.5 py-0.5 rounded-full border ${
                    isPassed
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : isSevere
                      ? 'bg-rose-100 text-rose-800 border-rose-300'
                      : 'bg-amber-100 text-amber-800 border-amber-300'
                  }`}
                >
                  {rule.status} • {rule.risk_level}
                </span>
              </div>

              <p className="text-xs text-slate-700 pl-6 leading-relaxed">
                {sanitizeSagarText(rule.details)}
              </p>

              {rule.evidence && Object.keys(rule.evidence).length > 0 && (
                <div className="mt-2.5 ml-6 pt-2 border-t border-sagar-borderLight flex flex-wrap gap-2 text-[11px] font-mono">
                  {Object.entries(rule.evidence).map(([key, val]) => (
                    <span
                      key={key}
                      className="px-2 py-0.5 rounded bg-white border border-sagar-border text-slate-700 shadow-soft-sm"
                    >
                      <strong className="text-slate-500 font-sans">{key.replace(/_/g, ' ')}:</strong>{' '}
                      <span className="text-sky-800 font-semibold">{String(val)}</span>
                    </span>
                  ))}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};
