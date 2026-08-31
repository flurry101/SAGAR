import React, { useState, useEffect } from 'react';
import { WifiOff, AlertTriangle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const OfflineBanner: React.FC = () => {
  const [isOffline, setIsOffline] = useState(
    typeof navigator !== 'undefined' ? !navigator.onLine : false
  );

  useEffect(() => {
    const handleOnline = () => setIsOffline(false);
    const handleOffline = () => setIsOffline(true);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  return (
    <AnimatePresence>
      {isOffline && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          className="bg-amber-50 border-b border-amber-300 text-amber-900 px-4 py-2 text-xs font-semibold flex items-center justify-center gap-2 sticky top-0 z-50 shadow-soft-sm"
        >
          <WifiOff className="w-4 h-4 text-amber-700 shrink-0" />
          <span>
            <strong>Offline Mode:</strong> Live sea state and atmospheric forecasts require an active connection. Showing cached vessel profile and offline guidance.
          </span>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
