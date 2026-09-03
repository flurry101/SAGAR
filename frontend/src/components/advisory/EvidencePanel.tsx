import React, { useState } from 'react';
import { RiskEvidence, EvidenceItem } from '../../types/risk';
import { HazardAlert } from './HazardAlert';
import { FileText, ChevronDown, ChevronUp, Database, ShieldCheck, Clock } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { Trans } from '@lingui/react/macro';

interface Props {
  riskEvidence: RiskEvidence;
  evidenceRegistry?: EvidenceItem[];
}

export const EvidencePanel: React.FC<Props> = ({ riskEvidence, evidenceRegistry = [] }) => {
  const [isOpen, setIsOpen] = useState(true);
  const [activeTab, setActiveTab] = useState<'triggers' | 'registry' | 'sources'>('triggers');

  const triggersCount = riskEvidence.hazard_flags?.length || 0;
  const registryCount = evidenceRegistry.length;

  return (
    <div className="bg-white border border-sagar-border rounded-2xl shadow-soft-sm overflow-hidden">
      {/* Header Bar */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full p-4 sm:p-5 flex items-center justify-between bg-white hover:bg-sagar-canvasAlt/70 transition-colors border-b border-sagar-borderLight text-left touch-target"
      >
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-sagar-powder border border-sky-200 flex items-center justify-center text-sky-700 shrink-0 font-bold">
            <FileText className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm sm:text-base font-bold text-sagar-navy">
              <Trans>Data Evidence & Operational Provenance ("See Why")</Trans>
            </h3>
            <p className="text-xs text-slate-500">
              <Trans>Verified dataset attribution, confidence ratings, and safety threshold triggers</Trans>
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-bold px-2.5 py-1 rounded-full bg-sagar-powder text-sky-800 border border-sky-200">
            <Trans>{triggersCount} Hazard Triggers</Trans>
          </span>
          {isOpen ? <ChevronUp className="w-5 h-5 text-slate-500" /> : <ChevronDown className="w-5 h-5 text-slate-500" />}
        </div>
      </button>

      {/* Panel Content with AnimatePresence */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="p-5 sm:p-6 space-y-5 overflow-hidden"
          >
            {/* Sub-tabs */}
            <div className="flex gap-2 border-b border-sagar-borderLight pb-3 text-xs">
              <button
                onClick={() => setActiveTab('triggers')}
                className={`px-3.5 py-1.5 rounded-lg font-bold transition-colors touch-target ${
                  activeTab === 'triggers'
                    ? 'bg-sagar-powder text-sky-900 border border-sky-200 shadow-soft-sm'
                    : 'text-slate-600 hover:text-sagar-navy'
                }`}
              >
                <Trans>Hazard Triggers ({triggersCount})</Trans>
              </button>
              {registryCount > 0 && (
                <button
                  onClick={() => setActiveTab('registry')}
                  className={`px-3.5 py-1.5 rounded-lg font-bold transition-colors touch-target ${
                    activeTab === 'registry'
                      ? 'bg-sagar-powder text-sky-900 border border-sky-200 shadow-soft-sm'
                      : 'text-slate-600 hover:text-sagar-navy'
                  }`}
                >
                  <Trans>Evidence Registry ({registryCount})</Trans>
                </button>
              )}
              <button
                onClick={() => setActiveTab('sources')}
                className={`px-3.5 py-1.5 rounded-lg font-bold transition-colors touch-target ${
                  activeTab === 'sources'
                    ? 'bg-sagar-powder text-sky-900 border border-sky-200 shadow-soft-sm'
                    : 'text-slate-600 hover:text-sagar-navy'
                }`}
              >
                <Trans>Attribution & Tiers</Trans>
              </button>
            </div>

            {/* 1. Triggers Tab */}
            {activeTab === 'triggers' && (
              <div className="space-y-3">
                {triggersCount === 0 ? (
                  <div className="flex items-center gap-3 p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs font-medium">
                    <ShieldCheck className="w-5 h-5 text-emerald-700 shrink-0" />
                    <span><Trans>No deterministic safety threshold violations were triggered across any leg of your trip.</Trans></span>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {riskEvidence.hazard_flags.map((h, i) => (
                      <HazardAlert key={i} hazard={h} />
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* 2. Evidence Registry Tab */}
            {activeTab === 'registry' && (
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3.5">
                {evidenceRegistry.map((item) => (
                  <div
                    key={item.evidence_id}
                    className="p-4 bg-sagar-canvasAlt border border-sagar-borderLight rounded-xl text-xs space-y-2"
                  >
                    <div className="flex items-center justify-between">
                      <span className="font-bold text-sky-900 capitalize">{item.category} <Trans>Agent</Trans></span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-white text-slate-700 border border-sagar-border font-mono font-semibold">
                        {typeof item.confidence === 'number' ? `${(item.confidence * 100).toFixed(0)}% Conf.` : item.confidence}
                      </span>
                    </div>

                    <div className="text-sm font-extrabold text-sagar-navy font-mono">
                      {item.value} <span className="text-xs font-normal text-slate-500 font-sans">{item.unit || ''}</span>
                    </div>

                    <div className="text-[11px] text-slate-500 space-y-0.5 pt-1.5 border-t border-sagar-borderLight">
                      <div className="truncate"><Trans>Source: </Trans><strong className="text-sagar-navy font-semibold">{item.source}</strong></div>
                      <div className="flex items-center gap-1 text-[10px] text-slate-500 font-mono">
                        <Clock className="w-3 h-3 text-sky-600" />
                        <span>{new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* 3. Attribution & Sources Tab */}
            {activeTab === 'sources' && (
              <div className="space-y-3">
                <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5 text-sky-600" />
                  <span><Trans>Dataset Attribution & Fallback Tiers:</Trans></span>
                </span>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {(riskEvidence.provenance_summary || []).map((prov, i) => (
                    <div
                      key={i}
                      className="p-3.5 bg-sagar-canvasAlt border border-sagar-borderLight rounded-xl text-xs flex items-center justify-between"
                    >
                      <div className="space-y-0.5 truncate max-w-[220px]">
                        <span className="text-sagar-navy font-bold block truncate">
                          {prov.source}
                        </span>
                        <span className="text-[10px] text-slate-500 block font-mono">
                          <Trans>Valid:</Trans> {prov.validity_time ? new Date(prov.validity_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : <Trans>Current model cycle</Trans>}
                        </span>
                      </div>
                      <span
                        className={`text-[10px] font-extrabold px-2.5 py-0.5 rounded-full border ${
                          prov.fallback_tier === 1
                            ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                            : prov.fallback_tier === 2
                            ? 'bg-amber-100 text-amber-800 border-amber-300'
                            : 'bg-orange-100 text-orange-800 border-orange-300'
                        }`}
                      >
                        {prov.fallback_tier === 1 ? <Trans>Tier 1 Live</Trans> : prov.fallback_tier === 2 ? <Trans>Tier 2 ML</Trans> : <Trans>Tier 3 Ref</Trans>} • {prov.confidence}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
