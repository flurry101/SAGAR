import React, { useState } from 'react';
import { TripContext } from '../../types/trip';
import { VesselProfile } from '../../types/vessel';
import { MapPin, Navigation, Clock, Ship, Check, Edit3, ArrowRight } from 'lucide-react';
import { motion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

interface Props {
  tripContext: Partial<TripContext>;
  vesselProfile?: VesselProfile;
  onConfirm: (updatedContext?: Partial<TripContext>) => void;
  onCancel?: () => void;
}

export const TripConfirmation: React.FC<Props> = ({
  tripContext,
  vesselProfile,
  onConfirm,
  onCancel
}) => {
  const { t } = useLingui();
  const [isEditing, setIsEditing] = useState(false);
  const [origin, setOrigin] = useState(tripContext.origin || '');
  const [departureTime, setDepartureTime] = useState(
    tripContext.departure_time_iso
      ? new Date(tripContext.departure_time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      : '05:00'
  );
  const [returnTime, setReturnTime] = useState(
    tripContext.expected_return_time_iso
      ? new Date(tripContext.expected_return_time_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })
      : '14:00'
  );
  const [destination, setDestination] = useState(
    tripContext.destination_name || ''
  );
  const [vesselType, setVesselType] = useState(
    vesselProfile?.vessel_type || 'Mechanized Trawler'
  );
  const [beamWidth, setBeamWidth] = useState(
    vesselProfile?.beam_width_m || 4.5
  );

  const handleConfirm = () => {
    // Preserve the original date from the context, or default to today
    const baseDepDate = tripContext.departure_time_iso ? new Date(tripContext.departure_time_iso) : new Date();
    const baseRetDate = tripContext.expected_return_time_iso ? new Date(tripContext.expected_return_time_iso) : new Date();
    
    const [depHours, depMinutes] = departureTime.split(':');
    baseDepDate.setHours(parseInt(depHours, 10), parseInt(depMinutes, 10), 0, 0);
    
    const [retHours, retMinutes] = returnTime.split(':');
    baseRetDate.setHours(parseInt(retHours, 10), parseInt(retMinutes, 10), 0, 0);

    onConfirm({
      origin,
      destination_name: destination,
      departure_time_iso: baseDepDate.toISOString(),
      expected_return_time_iso: baseRetDate.toISOString()
    });
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white border border-sagar-border rounded-2xl p-5 sm:p-6 shadow-soft-md space-y-4 my-3 text-sagar-navy max-w-xl mx-auto"
    >
      {/* Header */}
      <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
            <Check className="w-4 h-4" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-sagar-navy tracking-wide"><Trans>4D Voyage Plan Summary</Trans></h3>
            <p className="text-[11px] text-slate-500"><Trans>Please review what SAGAR understood before starting safety evaluation.</Trans></p>
          </div>
        </div>
        <button
          type="button"
          onClick={() => setIsEditing(!isEditing)}
          className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold bg-sagar-canvasAlt hover:bg-sagar-powder text-sky-800 border border-sagar-border transition-colors touch-target"
        >
          <Edit3 className="w-3.5 h-3.5" />
          <span>{isEditing ? <Trans>Done</Trans> : <Trans>Edit Details</Trans>}</span>
        </button>
      </div>

      {/* Grid of Trip Parameters */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
        {/* Origin */}
        <div className="p-3.5 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight space-y-1">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <MapPin className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Departure Harbor</Trans></span>
          </div>
          {isEditing ? (
            <input
              type="text"
              value={origin}
              onChange={(e) => setOrigin(e.target.value)}
              className="w-full bg-white border border-sagar-border rounded-md px-2 py-1.5 text-xs text-sagar-navy focus:outline-none focus:border-sky-500"
            />
          ) : (
            <p className="text-sm font-bold text-sagar-navy">{origin}</p>
          )}
        </div>

        {/* Destination */}
        <div className="p-3.5 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight space-y-1">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Navigation className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Operational Destination</Trans></span>
          </div>
          {isEditing ? (
            <input
              type="text"
              value={destination}
              onChange={(e) => setDestination(e.target.value)}
              className="w-full bg-white border border-sagar-border rounded-md px-2 py-1.5 text-xs text-sagar-navy focus:outline-none focus:border-sky-500"
            />
          ) : (
            <p className="text-sm font-bold text-sagar-navy">{destination}</p>
          )}
        </div>

        {/* Timing */}
        <div className="p-3.5 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight space-y-1">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Clock className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Schedule (Departure → Return)</Trans></span>
          </div>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <input
                type="time"
                value={departureTime}
                onChange={(e) => setDepartureTime(e.target.value)}
                className="bg-white border border-sagar-border rounded-md px-2 py-1 text-xs text-sagar-navy"
              />
              <span className="text-slate-500">→</span>
              <input
                type="time"
                value={returnTime}
                onChange={(e) => setReturnTime(e.target.value)}
                className="bg-white border border-sagar-border rounded-md px-2 py-1 text-xs text-sagar-navy"
              />
            </div>
          ) : (
            <p className="text-sm font-bold text-sagar-navy font-mono">
              {departureTime} IST <span className="text-slate-500 font-sans font-normal"><Trans>to</Trans></span> {returnTime} IST
            </p>
          )}
        </div>

        {/* Vessel */}
        <div className="p-3.5 rounded-xl bg-sagar-canvasAlt border border-sagar-borderLight space-y-1">
          <div className="flex items-center gap-1.5 text-slate-500 font-medium">
            <Ship className="w-3.5 h-3.5 text-sky-600" />
            <span><Trans>Vessel & Stability Baseline</Trans></span>
          </div>
          {isEditing ? (
            <div className="flex items-center gap-2">
              <input
                type="text"
                value={vesselType}
                onChange={(e) => setVesselType(e.target.value)}
                className="w-2/3 bg-white border border-sagar-border rounded-md px-2 py-1 text-xs text-sagar-navy"
              />
              <input
                type="number"
                step="0.1"
                value={beamWidth}
                onChange={(e) => setBeamWidth(parseFloat(e.target.value) || 4.5)}
                className="w-1/3 bg-white border border-sagar-border rounded-md px-2 py-1 text-xs text-sagar-navy"
                placeholder={t`Beam (m)`}
              />
            </div>
          ) : (
            <p className="text-sm font-bold text-sagar-navy">
              {vesselType} <span className="text-sky-800 font-mono text-xs">({beamWidth}m <Trans>beam</Trans>)</span>
            </p>
          )}
        </div>
      </div>

      {/* Safety Notice */}
      <div className="p-3 rounded-xl bg-sagar-powder/50 border border-sky-200 text-[11px] text-sky-950 flex items-center gap-2">
        <span className="text-sky-800 font-bold"><Trans>ℹ Note:</Trans></span>
        <span><Trans>SAGAR will correlate this 4D timeline with ocean wave forecasts and geofenced boundaries.</Trans></span>
      </div>

      {/* Action Buttons */}
      <div className="flex items-center gap-3 pt-1">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="flex-1 py-3 px-4 rounded-xl bg-sagar-canvasAlt hover:bg-slate-100 text-slate-700 font-bold text-xs border border-sagar-border transition-colors touch-target"
          >
            <Trans>Cancel</Trans>
          </button>
        )}
        <button
          type="button"
          onClick={handleConfirm}
          className="flex-1 py-3 px-4 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-soft-sm flex items-center justify-center gap-2 transition-all touch-target"
        >
          <span><Trans>Assess My Trip</Trans></span>
          <ArrowRight className="w-4 h-4" />
        </button>
      </div>
    </motion.div>
  );
};
