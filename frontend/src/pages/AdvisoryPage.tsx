import React, { useState } from 'react';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';
import { useAppStore } from '../state/appStore';
import { AdvisoryBanner } from '../components/advisory/AdvisoryBanner';
import { AdvisoryCard } from '../components/advisory/AdvisoryCard';
import { AlertBannerList } from '../components/advisory/AlertBannerList';
import { RouteComparisonCard } from '../components/advisory/RouteComparisonCard';
import { RuleResultsPanel } from '../components/advisory/RuleResultsPanel';
import { TripTimeline } from '../components/advisory/TripTimeline';
import { TrajectoryMap } from '../components/map/TrajectoryMap';
import { WeatherCard } from '../components/conditions/WeatherCard';
import { MarineCard } from '../components/conditions/MarineCard';
import { PFZSelector } from '../components/conditions/PFZSelector';
import { EvidencePanel } from '../components/advisory/EvidencePanel';
import { GeofenceWarning } from '../components/common/GeofenceWarning';
import { ConflictInfoCard } from '../components/advisory/ConflictInfoCard';
import { InsufficientInfo } from '../components/common/InsufficientInfo';
import { ModificationModal } from '../components/advisory/ModificationModal';
import { DisclaimerFooter } from '../components/common/DisclaimerFooter';
import { ScenarioSelector } from '../components/common/ScenarioSelector';
import { RefreshCw, ArrowLeft, Anchor, ShieldAlert, Waves } from 'lucide-react';
import { sanitizeSagarText, formatSagarDisclaimer } from '../utils/brand';
import { motion } from 'framer-motion';

export const AdvisoryPage: React.FC = () => {
  const { t } = useLingui();
  const { activeAssessment, setCurrentView } = useAppStore();
  const [isModifying, setIsModifying] = useState(false);

  const status = activeAssessment?.status;
  const data = activeAssessment?.data;

  if (status === 'insufficient_information') {
    return (
      <div className="space-y-4">
        <ScenarioSelector />
        <main className="max-w-7xl mx-auto px-4 py-4">
          <InsufficientInfo data={data as any} />
        </main>
      </div>
    );
  }

  if (status === 'error') {
    return (
      <div className="space-y-4">
        <ScenarioSelector />
        <main className="max-w-xl mx-auto my-12 p-8 bg-rose-50 border border-rose-300 rounded-2xl text-center space-y-4 shadow-soft-lg">
          <div className="w-12 h-12 rounded-xl bg-rose-100 text-rose-700 flex items-center justify-center mx-auto font-bold">
            <ShieldAlert className="w-6 h-6" />
          </div>
          <h1 className="text-lg font-extrabold text-rose-950"><Trans>Safety Decision Service Unavailable</Trans></h1>
          <p className="text-xs text-slate-700 leading-relaxed">
            {sanitizeSagarText(activeAssessment?.error?.message) || t`Unable to connect to SAGAR safety decision service. Please verify network connection and retry.`}
          </p>
          <button
            onClick={() => setCurrentView('chat')}
            className="px-6 py-3 rounded-xl bg-sky-600 hover:bg-sky-500 text-white font-bold text-xs shadow-soft-sm transition-all touch-target"
          >
            <Trans>Return to Trip Planner</Trans>
          </button>
        </main>
      </div>
    );
  }

  const advisory = data?.advisory;
  const trajectory = data?.trajectory;
  const riskEvidence = data?.risk_evidence;
  const vesselProfile = data?.vessel_profile;
  const weatherForecasts = data?.weather_forecasts;
  const marineObservations = data?.marine_observations;
  const pfzZones = data?.pfz_zones;
  const pfzAvailable = data?.pfz_available;
  const alerts = data?.alerts;
  const routeCandidates = data?.route_candidates;
  const visualizationSpec = data?.visualization_spec;
  const evidenceRegistry = data?.evidence_registry;
  const translationProvider = data?.translation_provider;

  // Max wave comparison for return-leg risk callout
  const returnHazard = riskEvidence?.hazard_flags?.find((h) => h.trip_phase === 'RETURN');

  return (
    <div className="space-y-4 pb-16">
      <ScenarioSelector />

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 space-y-6">
        {/* Navigation & Action Bar */}
        <div className="flex flex-wrap items-center justify-between gap-3">
          <button
            onClick={() => setCurrentView('chat')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-white hover:bg-sagar-canvasAlt text-sagar-navy text-xs font-bold border border-sagar-border transition-all shadow-soft-sm touch-target"
          >
            <ArrowLeft className="w-4 h-4 text-sky-600" />
            <span><Trans>Back to Trip Planner</Trans></span>
          </button>

          <div className="flex items-center gap-3">
            {translationProvider && (
              <span className="text-[10px] font-bold px-2.5 py-1 rounded-full bg-sagar-powder text-sky-900 border border-sky-200 font-mono">
                <Trans>Translation:</Trans> <strong className="text-sky-800 uppercase">{translationProvider}</strong>
              </span>
            )}
            <button
              onClick={() => setIsModifying(true)}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-sky-600 hover:bg-sky-500 text-white text-xs font-bold shadow-soft-sm transition-all touch-target"
            >
              <RefreshCw className="w-4 h-4" />
              <span><Trans>Modify Route or Return Time</Trans></span>
            </button>
          </div>
        </div>

        {/* 1. Primary Advisory Banner */}
        {advisory && (
          <AdvisoryBanner
            category={advisory.advisory_category}
            recommendationText={advisory.recommendation_text}
          />
        )}

        {/* Return-Trip Hazard Dedicated Insight Callout (if return hazard exists) */}
        {returnHazard && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            className="p-5 rounded-2xl bg-rose-50 border border-rose-300 shadow-soft-sm flex items-start gap-4"
          >
            <div className="w-10 h-10 rounded-xl bg-rose-100 text-rose-700 border border-rose-300 flex items-center justify-center shrink-0 mt-0.5">
              <Waves className="w-5 h-5" />
            </div>
            <div className="flex-1 text-xs space-y-1.5">
              <div className="flex items-center justify-between flex-wrap gap-2">
                <span className="font-extrabold text-rose-950 uppercase tracking-wide">
                  <Trans>Return Phase Spatio-Temporal Hazard Alert</Trans>
                </span>
                <span className="text-[10px] font-mono font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-900 border border-rose-300">
                  <Trans>SVAS Stability Threshold Breached</Trans>
                </span>
              </div>
              <p className="text-slate-800 leading-relaxed font-medium">
                <Trans>Outbound conditions at 05:00 departure may be calm, but afternoon wave height is forecasted to build to{' '}
                <strong className="text-rose-700 font-mono font-bold">{returnHazard.observed_value} m</strong> near the coastal approach by 16:00 return time, exceeding your boat’s physical capsize stability limit of{' '}
                <strong className="text-sagar-navy font-mono font-bold">{returnHazard.threshold_value} m</strong>.</Trans>
              </p>
            </div>
          </motion.div>
        )}

        {/* 2. Active Hazard Alerts */}
        {alerts && alerts.length > 0 && (
          <AlertBannerList alerts={alerts} />
        )}

        {/* Geofence & Data Conflict Panels */}
        {trajectory?.geofence_intersections && trajectory.geofence_intersections.length > 0 && (
          <GeofenceWarning intersections={trajectory.geofence_intersections} />
        )}

        {riskEvidence?.data_conflicts && riskEvidence.data_conflicts.length > 0 && (
          <ConflictInfoCard conflicts={riskEvidence.data_conflicts} />
        )}

        {/* 3. Scored Route Candidates Comparison */}
        {routeCandidates && routeCandidates.length > 0 && (
          <RouteComparisonCard routeCandidates={routeCandidates} />
        )}

        {/* 4. Map + 4D Timeline Operational Dashboard Split */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
          {/* Left Column: Interactive MapLibre Map & Conditions */}
          <div className="lg:col-span-7 space-y-5">
            <div className="bg-white border border-sagar-border rounded-2xl p-4 shadow-soft-sm">
              <div className="flex items-center justify-between mb-3 px-1">
                <div className="flex items-center gap-2 text-xs font-bold text-sagar-navy">
                  <Anchor className="w-4 h-4 text-sky-600" />
                  <span><Trans>Spatio-Temporal Trajectory & Environmental Layers</Trans></span>
                </div>
                <span className="text-[10px] text-slate-500 font-mono font-semibold">MapLibre GL 4D</span>
              </div>
              <TrajectoryMap
                trajectory={trajectory}
                hazardFlags={riskEvidence?.hazard_flags}
                pfzZones={pfzZones}
                visualizationSpec={visualizationSpec}
                routeCandidates={routeCandidates}
                weatherForecasts={weatherForecasts}
                marineObservations={marineObservations}
              />
            </div>

            {/* Candidate PFZs Comparison */}
            {pfzZones && pfzZones.length > 0 && (
              <PFZSelector pfzZones={pfzZones} />
            )}

            {/* Environmental Conditions */}
            <WeatherCard forecasts={weatherForecasts} />
            <MarineCard observations={marineObservations} pfzAvailable={pfzAvailable} />
          </div>

          {/* Right Column: Reasoning, Rules Engine & Timeline */}
          <div className="lg:col-span-5 space-y-5">
            {advisory && <AdvisoryCard advisory={advisory} vesselProfile={vesselProfile} />}
            {riskEvidence?.rule_results && (
              <RuleResultsPanel ruleResults={riskEvidence.rule_results} />
            )}
            {trajectory && (
              <TripTimeline trajectory={trajectory} hazardFlags={riskEvidence?.hazard_flags} />
            )}
          </div>
        </div>

        {/* 5. Evidence & Provenance Panel ("See Why") */}
        {riskEvidence && (
          <EvidencePanel
            riskEvidence={riskEvidence}
            evidenceRegistry={evidenceRegistry}
          />
        )}

        {/* 6. Decision Support Disclaimer Footer */}
        <DisclaimerFooter text={advisory?.disclaimer} />

        {/* Trip Modification Modal */}
        <ModificationModal isOpen={isModifying} onClose={() => setIsModifying(false)} />
      </main>
    </div>
  );
};
