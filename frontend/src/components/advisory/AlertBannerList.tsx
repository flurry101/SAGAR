import React from 'react';
import { AlertItem } from '../../types/risk';
import { ShieldAlert, Waves, Wind, Eye, CloudLightning } from 'lucide-react';
import { sanitizeSagarText } from '../../utils/brand';
import { Trans, useLingui } from '@lingui/react/macro';

interface Props {
  alerts?: AlertItem[];
}

export const AlertBannerList: React.FC<Props> = ({ alerts = [] }) => {
  const { t } = useLingui();
  if (!alerts || alerts.length === 0) {
    return (
      <div className="flex items-center gap-2 p-3.5 bg-white border border-sagar-border rounded-xl text-xs text-slate-700 shadow-soft-sm">
        <span className="w-2.5 h-2.5 rounded-full bg-emerald-500"></span>
        <span><Trans>No active extreme weather or maritime hazard alerts for this operational window.</Trans></span>
      </div>
    );
  }

  const getAlertIcon = (type: string) => {
    switch (type.toUpperCase()) {
      case 'HIGH_WAVE':
      case 'EXTREME_WAVE':
        return <Waves className="w-5 h-5 shrink-0" />;
      case 'STRONG_WIND':
      case 'EXTREME_WIND':
        return <Wind className="w-5 h-5 shrink-0" />;
      case 'LOW_VISIBILITY':
        return <Eye className="w-5 h-5 shrink-0" />;
      case 'CYCLONE':
        return <CloudLightning className="w-5 h-5 shrink-0" />;
      default:
        return <ShieldAlert className="w-5 h-5 shrink-0" />;
    }
  };

  return (
    <div className="space-y-2.5">
      <div className="flex items-center justify-between text-xs font-bold text-sagar-navy">
        <span className="flex items-center gap-1.5">
          <ShieldAlert className="w-4 h-4 text-amber-600" />
          <span><Trans>Active Hazard Alerts ({alerts.length})</Trans></span>
        </span>
        <span className="text-[10px] text-slate-500 font-mono"><Trans>Standard Maritime Thresholds</Trans></span>
      </div>

      <div className="space-y-2">
        {alerts.map((alert, idx) => {
          const isSevere = alert.severity === 'SEVERE';
          return (
            <div
              key={idx}
              className={`p-4 rounded-xl border flex items-start gap-3.5 shadow-soft-sm ${
                isSevere
                  ? 'bg-rose-50 border-rose-300 text-rose-950 hazard-pulse'
                  : 'bg-amber-50 border-amber-300 text-amber-950'
              }`}
            >
              <div className={`mt-0.5 ${isSevere ? 'text-rose-700' : 'text-amber-700'}`}>
                {getAlertIcon(alert.alert_type)}
              </div>

              <div className="flex-1 space-y-1">
                <div className="flex items-center justify-between gap-2 flex-wrap">
                  <span className="text-xs font-extrabold tracking-wide uppercase">
                    {alert.alert_type.replace(/_/g, ' ')}
                  </span>
                  <span
                    className={`text-[10px] font-black uppercase px-2.5 py-0.5 rounded-full border ${
                      isSevere
                        ? 'bg-rose-100 text-rose-900 border-rose-300'
                        : 'bg-amber-100 text-amber-900 border-amber-300'
                    }`}
                  >
                    {isSevere ? t`SEVERE HAZARD` : t`WARNING`}
                  </span>
                </div>

                <p className="text-xs font-semibold leading-relaxed text-slate-900">
                  {sanitizeSagarText(alert.message)}
                </p>

                {(alert.threshold !== undefined || alert.actual_value !== undefined) && (
                  <div className="flex items-center gap-4 text-[11px] pt-1 font-mono text-slate-700">
                    {alert.actual_value !== undefined && (
                      <span>
                        <Trans>Forecast: </Trans><strong className="text-sagar-navy">{alert.actual_value}</strong>
                      </span>
                    )}
                    {alert.threshold !== undefined && (
                      <span>
                        <Trans>Safe Limit: </Trans><strong className="text-sagar-navy">{alert.threshold}</strong>
                      </span>
                    )}
                  </div>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
