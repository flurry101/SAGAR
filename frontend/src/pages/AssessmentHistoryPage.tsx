import React from 'react';
import { useAppStore, HistoricalAssessment } from '../state/appStore';
import { History, Clock, MapPin, CheckCircle2, AlertTriangle, ShieldAlert, ArrowRight, Trash2, Shield, Navigation } from 'lucide-react';
import { sanitizeSagarText } from '../utils/brand';
import { motion } from 'framer-motion';

export const AssessmentHistoryPage: React.FC = () => {
  const { assessmentHistory, setActiveAssessment, setCurrentView, clearHistory } = useAppStore();

  const handleReplay = (item: HistoricalAssessment) => {
    setActiveAssessment(item.assessmentData);
    setCurrentView('advisory');
  };

  const getRiskBadge = (risk: string) => {
    switch (risk?.toUpperCase()) {
      case 'SAFE':
        return {
          bg: 'bg-emerald-100 text-emerald-800 border-emerald-300',
          icon: <CheckCircle2 className="w-3.5 h-3.5 text-emerald-700" />,
          label: 'SAFE'
        };
      case 'MODERATE':
      case 'ELEVATED':
        return {
          bg: 'bg-amber-100 text-amber-800 border-amber-300',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-amber-700" />,
          label: 'MODERATE'
        };
      case 'HIGH':
        return {
          bg: 'bg-orange-100 text-orange-800 border-orange-300',
          icon: <AlertTriangle className="w-3.5 h-3.5 text-orange-700" />,
          label: 'HIGH RISK'
        };
      case 'SEVERE':
        return {
          bg: 'bg-rose-100 text-rose-900 border-rose-300',
          icon: <ShieldAlert className="w-3.5 h-3.5 text-rose-700" />,
          label: 'SEVERE HAZARD'
        };
      default:
        return {
          bg: 'bg-slate-100 text-slate-800 border-slate-300',
          icon: <Shield className="w-3.5 h-3.5 text-slate-600" />,
          label: 'UNKNOWN'
        };
    }
  };

  return (
    <main className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6 text-sagar-navy">
      {/* Header */}
      <div className="bg-white border border-sagar-border rounded-2xl p-5 flex items-center justify-between shadow-soft-sm">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sagar-powder text-sky-700 flex items-center justify-center font-bold">
            <History className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-base sm:text-lg font-bold text-sagar-navy">Voyage Assessment History</h1>
            <p className="text-xs text-slate-500">
              Audit log of previous voyage safety evaluations and advisory outputs
            </p>
          </div>
        </div>

        {assessmentHistory.length > 0 && (
          <button
            onClick={clearHistory}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-sagar-canvasAlt hover:bg-rose-50 text-slate-600 hover:text-rose-700 text-xs border border-sagar-border hover:border-rose-200 transition-colors touch-target font-semibold"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>Clear History</span>
          </button>
        )}
      </div>

      {/* List */}
      {assessmentHistory.length === 0 ? (
        <div className="p-12 text-center bg-white border border-sagar-border rounded-2xl space-y-3 shadow-soft-sm">
          <div className="w-12 h-12 rounded-2xl bg-sagar-powder text-sky-700 flex items-center justify-center mx-auto font-bold">
            <Clock className="w-6 h-6" />
          </div>
          <h2 className="text-sm sm:text-base font-bold text-sagar-navy">No Previous Trip Assessments Found</h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            When you evaluate a voyage in the Trip Planner, the assessment parameters and safety advisories will be archived here.
          </p>
          <button
            onClick={() => setCurrentView('chat')}
            className="px-5 py-2.5 bg-sky-600 hover:bg-sky-500 text-white rounded-xl text-xs font-bold shadow-soft-sm transition-colors touch-target"
          >
            Plan a New Voyage
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {assessmentHistory.map((item) => {
            const badge = getRiskBadge(item.riskLevel);
            return (
              <motion.div
                key={item.id}
                onClick={() => handleReplay(item)}
                className="p-4 sm:p-5 rounded-2xl bg-white border border-sagar-border hover:border-sky-300 cursor-pointer transition-all space-y-3 group shadow-soft-sm touch-target"
                whileHover={{ y: -2 }}
                role="button"
                tabIndex={0}
                onKeyDown={(e) => e.key === 'Enter' && handleReplay(item)}
              >
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-sagar-borderLight pb-2.5">
                  <div className="flex items-center gap-2">
                    <span className={`inline-flex items-center gap-1 text-[10px] font-extrabold uppercase px-2.5 py-0.5 rounded-full border ${badge.bg}`}>
                      {badge.icon}
                      <span>{badge.label}</span>
                    </span>
                    <span className="text-xs text-slate-500 flex items-center gap-1 font-mono">
                      <Clock className="w-3.5 h-3.5 text-sky-600" />
                      <span>{new Date(item.timestamp).toLocaleString()}</span>
                    </span>
                  </div>

                  <span className="text-xs font-bold text-sky-700 group-hover:text-sky-900 flex items-center gap-1 self-start sm:self-auto">
                    <span>Inspect Advisory</span>
                    <ArrowRight className="w-3.5 h-3.5 group-hover:translate-x-1 transition-transform" />
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center gap-1.5 text-sagar-navy font-bold">
                      <MapPin className="w-3.5 h-3.5 text-sky-600" />
                      <span>{item.origin} → {item.destination}</span>
                    </div>
                    <p className="text-[11px] text-slate-500 font-mono">
                      Departure: {new Date(item.departureTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} • Return: {new Date(item.returnTime).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </p>
                  </div>

                  <div className="bg-sagar-canvasAlt p-3 rounded-xl border border-sagar-borderLight text-[11px] text-slate-700 line-clamp-2 font-medium">
                    {sanitizeSagarText(item.advisoryText)}
                  </div>
                </div>
              </motion.div>
            );
          })}
        </div>
      )}
    </main>
  );
};
