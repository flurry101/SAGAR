import React from 'react';
import { Trans } from '@lingui/react/macro';
import { GeofenceIntersection } from '../../types/trip';
import { ShieldAlert, MapPin } from 'lucide-react';

interface Props {
  intersections: GeofenceIntersection[];
}

export const GeofenceWarning: React.FC<Props> = ({ intersections }) => {
  if (!intersections || intersections.length === 0) return null;

  return (
    <div className="bg-rose-50 border border-rose-300 rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-3.5">
      <div className="flex items-center gap-2.5 text-rose-950 font-extrabold text-sm border-b border-rose-200 pb-3">
        <ShieldAlert className="w-5 h-5 text-rose-700 shrink-0" />
        <span><Trans>GEOFENCE WARNING: Restricted Marine Zone Intersection</Trans></span>
      </div>

      {intersections.map((geo, idx) => (
        <div key={idx} className="bg-white p-4 rounded-xl border border-rose-200 space-y-2 text-xs shadow-soft-sm">
          <div className="flex items-center justify-between text-rose-950 font-bold">
            <span className="flex items-center gap-1.5">
              <MapPin className="w-3.5 h-3.5 text-rose-700" />
              <span>{geo.constraint_name}</span>
            </span>
            <span className="px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-900 border border-rose-300 text-[10px] font-mono font-bold">
              {geo.constraint_type}
            </span>
          </div>

          <p className="text-slate-800 leading-relaxed font-medium">
            <Trans>
              Your planned route trajectory intersects this protected boundary at waypoint indices{' '}
              <strong className="text-rose-700 font-mono font-bold">{geo.affected_waypoints?.join(', ')}</strong>. Navigation and harvesting inside this zone are restricted under national maritime and environmental regulations.
            </Trans>
          </p>

          <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1.5 border-t border-sagar-borderLight">
            <span><Trans>GIS Source:</Trans> <strong className="text-sagar-navy">{geo.source}</strong></span>
            <span className="text-sky-800 font-bold"><Trans>Suggested Action: Select coastal or offshore bypass corridor</Trans></span>
          </div>
        </div>
      ))}
    </div>
  );
};
