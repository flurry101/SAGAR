import React, { useState } from 'react';
import { useAppStore } from '../../state/appStore';
import { tripApi } from '../../api/tripApi';
import { X, RefreshCw, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface Props {
  isOpen: boolean;
  onClose: () => void;
}

export const ModificationModal: React.FC<Props> = ({ isOpen, onClose }) => {
  const { activeAssessment, setActiveAssessment } = useAppStore();
  const tripContext = activeAssessment?.data?.trip_context;

  const [departureTime, setDepartureTime] = useState('05:00');
  const [returnTime, setReturnTime] = useState('12:00');
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleApplyModification = async (e?: React.FormEvent, customReturn?: string) => {
    if (e) e.preventDefault();
    setLoading(true);

    const effectiveReturn = customReturn || returnTime;
    const message = `Modify trip parameters: Departure at ${departureTime} from ${
      tripContext?.origin || 'Mangalore Port'
    }, return earlier at ${effectiveReturn} IST to avoid return wave hazard.`;

    try {
      const response = await tripApi.assessTrip({
        message,
        session_id: `sess-mod-${Date.now()}`
      });

      if (response.status === 'success' || response.status === 'insufficient_information') {
        setActiveAssessment(response);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
      onClose();
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-sagar-navy/60 backdrop-blur-sm flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        exit={{ opacity: 0, scale: 0.95 }}
        className="bg-white border border-sagar-border rounded-2xl max-w-md w-full p-6 shadow-soft-xl space-y-5 text-sagar-navy"
      >
        <div className="flex items-center justify-between border-b border-sagar-borderLight pb-3">
          <div className="flex items-center gap-2 text-sky-800 font-bold text-sm">
            <RefreshCw className="w-4 h-4 text-sky-600" />
            <span>Modify Voyage Timing & Route</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-slate-400 hover:text-sagar-navy transition-colors touch-target"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Quick Suggestion Presets */}
        <div className="space-y-2">
          <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">
            Suggested Mitigations:
          </span>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => {
                setReturnTime('12:00');
                handleApplyModification(undefined, '12:00');
              }}
              className="p-3 rounded-xl bg-sagar-canvasAlt hover:bg-sagar-powder border border-sagar-borderLight text-sky-900 font-semibold text-left transition-colors touch-target shadow-soft-sm"
            >
              <div className="font-bold">Return at 12:00 PM</div>
              <div className="text-[10px] text-slate-500">Beat afternoon wave surge</div>
            </button>

            <button
              type="button"
              onClick={() => {
                setReturnTime('13:00');
                handleApplyModification(undefined, '13:00');
              }}
              className="p-3 rounded-xl bg-sagar-canvasAlt hover:bg-sagar-powder border border-sagar-borderLight text-sky-900 font-semibold text-left transition-colors touch-target shadow-soft-sm"
            >
              <div className="font-bold">Return at 1:00 PM</div>
              <div className="text-[10px] text-slate-500">Reduce return exposure</div>
            </button>
          </div>
        </div>

        <form onSubmit={(e) => handleApplyModification(e)} className="space-y-4 pt-2 border-t border-sagar-borderLight">
          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1.5 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              <span>Custom Departure Time (IST):</span>
            </label>
            <input
              type="time"
              value={departureTime}
              onChange={(e) => setDepartureTime(e.target.value)}
              className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2.5 text-sm text-sagar-navy focus:border-sky-500 focus:outline-none font-mono"
            />
          </div>

          <div>
            <label className="text-xs font-semibold text-slate-700 block mb-1.5 flex items-center gap-1.5">
              <Clock className="w-3.5 h-3.5 text-sky-600" />
              <span>Custom Expected Return Time (IST):</span>
            </label>
            <input
              type="time"
              value={returnTime}
              onChange={(e) => setReturnTime(e.target.value)}
              className="w-full bg-white border border-sagar-border rounded-xl px-3 py-2.5 text-sm text-sagar-navy focus:border-sky-500 focus:outline-none font-mono"
            />
            <p className="text-[11px] text-sky-800 mt-1.5 leading-relaxed font-medium">
              Note: Changing return timing recalculates sea state wave heights for every waypoint along the return route.
            </p>
          </div>

          <div className="pt-2 flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-3 rounded-xl bg-sagar-canvasAlt hover:bg-slate-100 text-slate-700 text-xs font-bold border border-sagar-border transition-colors touch-target"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className="flex-1 px-4 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow-soft-sm disabled:opacity-50 transition-all touch-target"
            >
              {loading ? 'Re-evaluating...' : 'Re-assess Voyage'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
};
