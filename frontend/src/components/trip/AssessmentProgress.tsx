import React, { useEffect, useState } from 'react';
import { CheckCircle2, Clock, Loader2, Shield, Compass, Waves, CloudRain, FileCheck, Navigation } from 'lucide-react';
import { motion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

interface Step {
  id: string;
  label: string;
  sublabel: string;
  icon: React.ReactNode;
}

const getSteps = (t: any): Step[] => [
  { id: '1', label: t`Understanding your trip`, sublabel: t`Extracting departure, destination & vessel schedule`, icon: <Compass className="w-4 h-4" /> },
  { id: '2', label: t`Finding your fishing zone`, sublabel: t`Querying PFZ thermal & chlorophyll coordinates`, icon: <Waves className="w-4 h-4" /> },
  { id: '3', label: t`Calculating your route`, sublabel: t`Generating 4D waypoints and transit ETAs`, icon: <Navigation className="w-4 h-4" /> },
  { id: '4', label: t`Checking sea conditions`, sublabel: t`Retrieving marine wave and current observations`, icon: <Waves className="w-4 h-4" /> },
  { id: '5', label: t`Checking weather forecast`, sublabel: t`Evaluating wind, wave & swell across all trip phases`, icon: <CloudRain className="w-4 h-4" /> },
  { id: '6', label: t`Assessing safety`, sublabel: t`Applying deterministic SVAS vessel stability limits`, icon: <Shield className="w-4 h-4" /> },
  { id: '7', label: t`Preparing your advisory`, sublabel: t`Formulating explainable recommendations & evidence`, icon: <FileCheck className="w-4 h-4" /> }
];

interface Props {
  onComplete?: () => void;
  speedMs?: number;
}

export const AssessmentProgress: React.FC<Props> = ({ onComplete, speedMs = 350 }) => {
  const { t } = useLingui();
  const STEPS = getSteps(t);
  const [currentStepIndex, setCurrentStepIndex] = useState(0);

  useEffect(() => {
    if (currentStepIndex < STEPS.length) {
      const timer = setTimeout(() => {
        setCurrentStepIndex((prev) => prev + 1);
      }, speedMs);
      return () => clearTimeout(timer);
    } else {
      if (onComplete) {
        const completeTimer = setTimeout(() => {
          onComplete();
        }, 250);
        return () => clearTimeout(completeTimer);
      }
    }
  }, [currentStepIndex, speedMs, onComplete, STEPS.length]);

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.98 }}
      animate={{ opacity: 1, scale: 1 }}
      className="bg-white border border-sagar-border rounded-2xl p-6 shadow-soft-md space-y-5 my-4 max-w-lg mx-auto"
    >
      <div className="flex items-center gap-3 border-b border-sagar-borderLight pb-3">
        <div className="w-9 h-9 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
          <Loader2 className="w-5 h-5 animate-spin" />
        </div>
        <div>
          <h3 className="text-sm font-bold text-sagar-navy tracking-wide"><Trans>Evaluating Spatio-Temporal Safety</Trans></h3>
          <p className="text-xs text-slate-500"><Trans>SAGAR is checking sea state and boat stability limits across all legs.</Trans></p>
        </div>
      </div>

      {/* Step Checklist */}
      <div className="space-y-2.5">
        {STEPS.map((step, idx) => {
          const isDone = idx < currentStepIndex;
          const isCurrent = idx === currentStepIndex;

          return (
            <div
              key={step.id}
              className={`flex items-center justify-between p-3 rounded-xl border transition-all text-xs ${
                isDone
                  ? 'bg-emerald-50/40 border-emerald-200 text-sagar-navy'
                  : isCurrent
                  ? 'bg-sagar-powder/60 border-sky-300 text-sky-950 shadow-soft-sm'
                  : 'bg-sagar-canvasAlt/50 border-sagar-borderLight text-slate-400'
              }`}
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-6 h-6 rounded-lg flex items-center justify-center shrink-0 ${
                    isDone
                      ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                      : isCurrent
                      ? 'bg-sky-100 text-sky-800 border border-sky-300 animate-pulse'
                      : 'bg-white text-slate-400 border border-sagar-border'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-700" />
                  ) : isCurrent ? (
                    <Loader2 className="w-3.5 h-3.5 animate-spin text-sky-700" />
                  ) : (
                    <span className="text-[10px] font-bold">{idx + 1}</span>
                  )}
                </div>

                <div>
                  <span className={`font-bold block ${isCurrent ? 'text-sky-900' : isDone ? 'text-sagar-navy' : 'text-slate-500'}`}>
                    {step.label}
                  </span>
                  <span className="text-[10px] text-slate-500 block">{step.sublabel}</span>
                </div>
              </div>

              <div>
                {isDone && (
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 border border-emerald-300">
                    <Trans>Done</Trans>
                  </span>
                )}
                {isCurrent && (
                  <span className="text-[10px] font-extrabold px-2.5 py-0.5 rounded-full bg-sky-100 text-sky-800 border border-sky-300 animate-pulse">
                    <Trans>Evaluating...</Trans>
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>

      <div className="text-center pt-1">
        <p className="text-[11px] text-slate-500 flex items-center justify-center gap-1.5">
          <Clock className="w-3.5 h-3.5 text-sky-600" />
          <span><Trans>Processing forecast models & deterministic SVAS stability rules...</Trans></span>
        </p>
      </div>
    </motion.div>
  );
};
