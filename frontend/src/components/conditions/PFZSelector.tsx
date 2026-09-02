import React, { useState } from 'react';
import { PFZZone } from '../../types/api';
import { Waves, Navigation, Check, Info } from 'lucide-react';
import { motion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';

interface Props {
  pfzZones?: PFZZone[];
  selectedPfzId?: string;
  onSelectPfz?: (pfz: PFZZone) => void;
}

export const PFZSelector: React.FC<Props> = ({
  pfzZones = [],
  selectedPfzId,
  onSelectPfz
}) => {
  const [activeId, setActiveId] = useState<string>(selectedPfzId || pfzZones[0]?.pfz_id || '');

  if (!pfzZones || pfzZones.length === 0) {
    return null;
  }

  const handleSelect = (pfz: PFZZone) => {
    setActiveId(pfz.pfz_id);
    if (onSelectPfz) {
      onSelectPfz(pfz);
    }
  };

  return (
    <div className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-sm space-y-4">
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2 text-sagar-navy font-bold text-xs sm:text-sm">
          <Waves className="w-4 h-4 text-emerald-600" />
          <span><Trans>Candidate Potential Fishing Zones (PFZ)</Trans></span>
        </div>
        <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
          <Trans>{pfzZones.length} Zones Available</Trans>
        </span>
      </div>

      <div className="p-3.5 bg-sagar-powder/50 border border-sky-200 rounded-xl text-xs text-sky-950 space-y-1">
        <div className="flex items-center gap-1.5 text-sky-800 font-bold text-xs">
          <Info className="w-3.5 h-3.5 shrink-0" />
          <span><Trans>Oceanographic Aggregation Signals</Trans></span>
        </div>
        <p className="text-[11px] text-slate-700 leading-relaxed font-normal">
          <Trans>PFZs identify thermal boundaries and chlorophyll fronts derived from satellite data. They indicate higher probability of pelagic fish aggregation, but do not guarantee catch.</Trans>
        </p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3.5">
        {pfzZones.map((pfz) => {
          const isSelected = activeId === pfz.pfz_id;

          return (
            <motion.div
              key={pfz.pfz_id}
              onClick={() => handleSelect(pfz)}
              className={`cursor-pointer p-4 rounded-xl border transition-all space-y-2.5 touch-target ${
                isSelected
                  ? 'bg-emerald-50/50 border-emerald-400 ring-2 ring-emerald-300 shadow-soft-sm'
                  : 'bg-white border-sagar-borderLight hover:bg-sagar-canvasAlt/80 hover:border-sagar-border'
              }`}
              whileHover={{ y: -2 }}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => e.key === 'Enter' && handleSelect(pfz)}
            >
              <div className="flex items-center justify-between">
                <span className="font-bold text-xs text-sagar-navy flex items-center gap-1.5">
                  <Navigation className="w-3.5 h-3.5 text-emerald-600" />
                  <span>{pfz.pfz_id}</span>
                </span>
                {isSelected ? (
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300 flex items-center gap-1">
                    <Check className="w-3 h-3 text-emerald-700" />
                    <span><Trans>Selected</Trans></span>
                  </span>
                ) : (
                  <span className="text-[10px] text-slate-500 px-2 py-0.5 rounded-full bg-sagar-canvasAlt border border-sagar-border">
                    <Trans>Candidate</Trans>
                  </span>
                )}
              </div>

              <div className="grid grid-cols-2 gap-2 text-[11px] font-mono">
                <div className="bg-sagar-canvasAlt p-2.5 rounded-lg border border-sagar-borderLight">
                  <span className="text-slate-500 block text-[10px] font-sans"><Trans>Offshore Distance</Trans></span>
                  <span className="text-sagar-navy font-bold">{pfz.distance_from_origin_km} km</span>
                </div>
                <div className="bg-sagar-canvasAlt p-2.5 rounded-lg border border-sagar-borderLight">
                  <span className="text-slate-500 block text-[10px] font-sans"><Trans>Coordinates</Trans></span>
                  <span className="text-sagar-navy font-bold">
                    {pfz.coordinates.lat.toFixed(2)}°N, {pfz.coordinates.lon.toFixed(2)}°E
                  </span>
                </div>
              </div>

              <div className="text-[10px] text-slate-500 flex items-center justify-between pt-1 border-t border-sagar-borderLight">
                <span><Trans>Valid:</Trans> {new Date(pfz.valid_until).toLocaleDateString()}</span>
                <span className="text-emerald-700 font-bold"><Trans>Route Verified</Trans></span>
              </div>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
};
