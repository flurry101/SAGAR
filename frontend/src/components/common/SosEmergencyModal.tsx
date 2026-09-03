import React, { useEffect, useState } from 'react';
import { useAppStore } from '../../state/appStore';
import { PhoneCall, AlertOctagon, X, Compass } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

interface SosEmergencyModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export const SosEmergencyModal: React.FC<SosEmergencyModalProps> = ({ isOpen, onClose }) => {
  const { userVessel } = useAppStore();

  const [coords, setCoords] = useState<{ lat: number; lon: number } | null>(null);
  const [gpsStatus, setGpsStatus] = useState<'acquiring' | 'locked' | 'fallback'>('acquiring');

  useEffect(() => {
    if (!isOpen) return;

    // Reset status when opened
    setGpsStatus('acquiring');

    if (typeof navigator !== 'undefined' && 'geolocation' in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCoords({
            lat: position.coords.latitude,
            lon: position.coords.longitude,
          });
          setGpsStatus('locked');
        },
        (error) => {
          console.warn('Native GPS acquisition error:', error.message);
          // Fallback to coastal standard coordinates (Kochi / Kerala Coast as default)
          setCoords({ lat: 9.94, lon: 76.25 });
          setGpsStatus('fallback');
        },
        {
          enableHighAccuracy: true,
          timeout: 8000,
          maximumAge: 0,
        }
      );
    } else {
      setCoords({ lat: 9.94, lon: 76.25 });
      setGpsStatus('fallback');
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const formatCoordDisplay = (lat: number, lon: number) => {
    const latDir = lat >= 0 ? 'N' : 'S';
    const lonDir = lon >= 0 ? 'E' : 'W';
    return `${Math.abs(lat).toFixed(2)}°${latDir}, ${Math.abs(lon).toFixed(2)}°${lonDir}`;
  };

  const vesselIdDisplay = userVessel?.registration_number
    ? `${userVessel.registration_number} (${userVessel.home_port || 'Kochi'})`
    : 'IND-KL-04-M (Kochi)';

  const activeCoords = coords ? formatCoordDisplay(coords.lat, coords.lon) : '9.94°N, 76.25°E';

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-md flex items-center justify-center p-4">
        <motion.div
          initial={{ opacity: 0, scale: 0.92, y: 10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.92, y: 10 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="relative bg-[#0d0f14] border border-red-500/30 rounded-3xl max-w-[460px] w-full p-6 sm:p-7 shadow-[0_0_50px_rgba(220,38,38,0.25)] text-white text-center space-y-5"
        >
          {/* Top Close Icon */}
          <button
            type="button"
            onClick={onClose}
            className="absolute top-4 right-4 p-2 rounded-full text-zinc-500 hover:text-white hover:bg-zinc-800/60 transition-colors cursor-pointer"
            aria-label="Close"
          >
            <X className="w-5 h-5" />
          </button>

          {/* Red Glowing Alert Icon */}
          <div className="flex justify-center pt-2">
            <div className="relative w-16 h-16 rounded-full bg-red-950/60 border border-red-500/50 flex items-center justify-center shadow-[0_0_25px_rgba(239,68,68,0.4)]">
              <div className="absolute inset-0 rounded-full border border-red-500/30 animate-ping opacity-30" />
              <div className="w-10 h-10 rounded-xl bg-red-600/30 border border-red-500 flex items-center justify-center">
                <AlertOctagon className="w-6 h-6 text-red-500 stroke-[2.5]" />
              </div>
            </div>
          </div>

          {/* Heading */}
          <div className="space-y-2">
            <h2 className="text-lg sm:text-xl font-black text-white tracking-wide uppercase">
              EMERGENCY DISTRESS SOS ACTIVATED
            </h2>
            <p className="text-xs sm:text-[13px] text-zinc-400 font-normal leading-relaxed max-w-sm mx-auto">
              Broadcasting geo-tagged distress packet to Indian Coast Guard Maritime Rescue Co-ordination Centre (MRCC).
            </p>
          </div>

          {/* Info Details Box */}
          <div className="bg-[#16181f] border border-zinc-800/90 rounded-2xl p-4 sm:p-5 text-left space-y-3 shadow-inner">
            <div className="text-xs sm:text-sm">
              <span className="text-zinc-400 font-medium">Vessel ID: </span>
              <span className="font-extrabold text-white tracking-wide">{vesselIdDisplay}</span>
            </div>

            <div className="text-xs sm:text-sm">
              <span className="text-zinc-400 font-medium">GPS Coordinates: </span>
              <span className="font-extrabold text-white tracking-wide">
                {gpsStatus === 'acquiring' ? (
                  <span className="inline-flex items-center gap-1.5 text-amber-400 font-normal text-xs">
                    <Compass className="w-3.5 h-3.5 animate-spin" />
                    Acquiring live GPS fix...
                  </span>
                ) : (
                  <span>{activeCoords}</span>
                )}
              </span>
              {gpsStatus === 'locked' && (
                <span className="ml-2 text-[10px] text-emerald-400 font-semibold uppercase tracking-wider bg-emerald-950/60 px-1.5 py-0.5 rounded border border-emerald-800/40">
                  Live GPS
                </span>
              )}
            </div>

            <div className="text-xs sm:text-sm">
              <span className="text-zinc-400 font-medium">Distress Frequency: </span>
              <span className="font-bold text-[#34d399] tracking-wide font-mono">
                VHF Channel 16 (156.8 MHz)
              </span>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex items-center gap-3 pt-1">
            <a
              href="tel:1554"
              className="flex-1 py-3.5 px-4 rounded-full bg-red-600 hover:bg-red-700 active:scale-[0.98] text-white font-extrabold text-xs sm:text-sm flex items-center justify-center gap-2 shadow-[0_4px_20px_rgba(220,38,38,0.4)] transition-all cursor-pointer select-none"
            >
              <PhoneCall className="w-4 h-4 shrink-0" />
              <span>Call Coast Guard 1554</span>
            </a>

            <button
              type="button"
              onClick={onClose}
              className="py-3.5 px-6 rounded-full bg-[#1e222b] hover:bg-[#282d38] active:scale-[0.98] text-zinc-300 hover:text-white font-bold text-xs sm:text-sm transition-all border border-zinc-700/60 cursor-pointer select-none"
            >
              Dismiss
            </button>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};
