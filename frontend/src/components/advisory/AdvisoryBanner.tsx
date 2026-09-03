import React from 'react';
import { AdvisoryCategory } from '../../types/risk';
import { CheckCircle2, AlertTriangle, ShieldAlert, HelpCircle, RefreshCw } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';
import { useLingui } from '@lingui/react/macro';

interface Props {
  category: AdvisoryCategory;
  recommendationText: string;
}

export const AdvisoryBanner: React.FC<Props> = ({ category, recommendationText }) => {
  const { t } = useLingui();
  const getCategoryConfig = (cat: AdvisoryCategory) => {
    switch (cat) {
      case 'CONDITIONS_FAVORABLE':
        return {
          bg: 'bg-emerald-50 border-emerald-300 text-emerald-950',
          badgeBg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          icon: <CheckCircle2 className="w-6 h-6 text-emerald-700 shrink-0" />,
          title: t`SAFE — CONDITIONS FAVORABLE`
        };
      case 'GO_WITH_CAUTION':
      case 'ELEVATED_RISK_IDENTIFIED':
        return {
          bg: 'bg-amber-50 border-amber-300 text-amber-950',
          badgeBg: 'bg-amber-100 text-amber-800 border-amber-300',
          icon: <AlertTriangle className="w-6 h-6 text-amber-700 shrink-0" />,
          title: t`MODERATE RISK — PROCEED WITH CAUTION`
        };
      case 'CONSIDER_ROUTE_TIME_MODIFICATION':
        return {
          bg: 'bg-orange-50 border-orange-300 text-orange-950',
          badgeBg: 'bg-orange-100 text-orange-800 border-orange-300',
          icon: <RefreshCw className="w-6 h-6 text-orange-700 shrink-0" />,
          title: t`HIGH RISK — ROUTE OR TIME MODIFICATION RECOMMENDED`
        };
      case 'SEVERE_HAZARD_OVERLAP':
        return {
          bg: 'bg-rose-50 border-rose-400 text-rose-950 hazard-pulse',
          badgeBg: 'bg-rose-100 text-rose-900 border-rose-300',
          icon: <ShieldAlert className="w-6 h-6 text-rose-700 shrink-0" />,
          title: t`SEVERE HAZARD DETECTED — VOYAGE NOT RECOMMENDED`
        };
      case 'INSUFFICIENT_INFORMATION':
      default:
        return {
          bg: 'bg-slate-50 border-slate-300 text-slate-900',
          badgeBg: 'bg-slate-100 text-slate-800 border-slate-300',
          icon: <HelpCircle className="w-6 h-6 text-slate-600 shrink-0" />,
          title: t`INSUFFICIENT DATA — UNABLE TO SAFELY ASSESS VOYAGE`
        };
    }
  };

  const config = getCategoryConfig(category);

  return (
    <div className={`p-5 rounded-2xl border shadow-soft-sm ${config.bg}`}>
      <div className="flex items-start gap-4">
        {config.icon}
        <div className="flex-1">
          <div className="flex items-center gap-2 flex-wrap mb-1">
            <span className={`text-[11px] font-extrabold px-2.5 py-0.5 rounded-full border uppercase tracking-wider ${config.badgeBg}`}>
              {config.title}
            </span>
          </div>
          <p className="text-sm sm:text-base font-bold leading-relaxed mt-1.5 text-slate-900">
            {sanitizeSagarText(recommendationText)}
          </p>
        </div>
      </div>
    </div>
  );
};
