import React, { useState, useEffect, useRef } from 'react';
import { Mic, Square, Loader2, Volume2, AlertCircle } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { VexylClient, VoiceState } from './vexylClient';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

export const VoiceWidget: React.FC = () => {
  const { t } = useLingui();
  const [state, setState] = useState<VoiceState>('idle');
  const [errorMessage, setErrorMessage] = useState('');
  const clientRef = useRef<VexylClient | null>(null);

  const handleStart = async () => {
    setErrorMessage('');
    const wsUrl = import.meta.env.VITE_VEXYL_WS_URL || 'ws://localhost:8082';
    
      clientRef.current = new VexylClient({
        wsUrl,
        onStateChange: (newState) => setState(newState),
        onError: (err) => {
          setErrorMessage(t`Voice unavailable`);
          setState('error');
        }
      });

      await clientRef.current.start();
    };

    const handleStop = () => {
      if (clientRef.current) {
        clientRef.current.stop();
        clientRef.current = null;
      }
      setState('idle');
    };

    useEffect(() => {
      return () => {
        if (clientRef.current) {
          clientRef.current.stop();
        }
      };
    }, []);

    const renderContent = () => {
      if (state === 'idle') {
         return (
           <button 
             onClick={handleStart} 
             className="w-14 h-14 bg-sky-600 hover:bg-sky-500 text-white rounded-full flex items-center justify-center shadow-soft-xl border border-white/20 transition-all active:scale-95"
             aria-label={t`Start Voice Assistant`}
           >
              <Mic className="w-6 h-6" />
           </button>
         );
      }

      return (
        <div className="flex items-center gap-3 bg-white p-3 rounded-full shadow-soft-xl border border-sagar-border pr-4">
           <div className="flex items-center justify-center w-10 h-10 rounded-full bg-sky-50 text-sky-600 relative">
              {state === 'connecting' && <Loader2 className="w-5 h-5 animate-spin" />}
              {state === 'listening' && (
                <span className="flex h-3 w-3 relative">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                  <span className="relative inline-flex rounded-full h-3 w-3 bg-red-500"></span>
                </span>
              )}
              {state === 'processing' && <Loader2 className="w-5 h-5 animate-spin" />}
              {state === 'speaking' && <Volume2 className="w-5 h-5 animate-pulse" />}
              {state === 'error' && <AlertCircle className="w-5 h-5 text-red-500" />}
           </div>
           
           <div className="flex-1 min-w-[120px]">
             <p className="text-sm font-medium text-slate-800 capitalize">
               {state === 'error' ? errorMessage : (state === 'connecting' ? <Trans>connecting...</Trans> : state === 'listening' ? <Trans>listening...</Trans> : state === 'processing' ? <Trans>processing...</Trans> : state === 'speaking' ? <Trans>speaking...</Trans> : state)}
             </p>
           </div>

           <button 
             onClick={handleStop} 
             className="w-10 h-10 bg-slate-100 hover:bg-slate-200 text-slate-600 rounded-full flex items-center justify-center transition-colors active:scale-95"
             aria-label={t`Stop Voice Assistant`}
           >
              <Square className="w-4 h-4 fill-current" />
           </button>
        </div>
      );
    };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      <AnimatePresence mode="wait">
         <motion.div
            key={state === 'idle' ? 'idle' : 'active'}
            initial={{ scale: 0.8, opacity: 0, y: 10 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.8, opacity: 0, y: 10 }}
            transition={{ type: 'spring', stiffness: 400, damping: 25 }}
         >
            {renderContent()}
         </motion.div>
      </AnimatePresence>
    </div>
  );
};
