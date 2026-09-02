import os
import re

def update_file(path, replacements):
    with open(path, 'r') as f:
        content = f.read()
    for old, new in replacements:
        content = content.replace(old, new)
    with open(path, 'w') as f:
        f.write(content)

# AdvisoryCard.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/AdvisoryCard.tsx', [
    ("import { sanitizeSagarText } from '../../utils/brand';", "import { sanitizeSagarText } from '../../utils/brand';\nimport { Trans } from '@lingui/react/macro';"),
    ("<span>Safety Reasoning & Context</span>", "<span><Trans>Safety Reasoning & Context</Trans></span>"),
    ("Affected: {advisory.affected_phase}", "<Trans>Affected: {advisory.affected_phase}</Trans>"),
    ("Primary Safety Factor:", "<Trans>Primary Safety Factor:</Trans>"),
    ("Vessel Stability Context:", "<Trans>Vessel Stability Context:</Trans>"),
    ("Critical Time Window", "<Trans>Critical Time Window</Trans>"),
    ("Critical Zone", "<Trans>Critical Zone</Trans>")
])

# AlertBannerList.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/AlertBannerList.tsx', [
    ("import { sanitizeSagarText } from '../../utils/brand';", "import { sanitizeSagarText } from '../../utils/brand';\nimport { Trans, useLingui } from '@lingui/react/macro';"),
    ("export const AlertBannerList: React.FC<Props> = ({ alerts = [] }) => {", "export const AlertBannerList: React.FC<Props> = ({ alerts = [] }) => {\n  const { t } = useLingui();"),
    ("<span>No active extreme weather or maritime hazard alerts for this operational window.</span>", "<span><Trans>No active extreme weather or maritime hazard alerts for this operational window.</Trans></span>"),
    ("<span>Active Hazard Alerts ({alerts.length})</span>", "<span><Trans>Active Hazard Alerts ({alerts.length})</Trans></span>"),
    (">Standard Maritime Thresholds<", "><Trans>Standard Maritime Thresholds</Trans><"),
    ("{isSevere ? 'SEVERE HAZARD' : 'WARNING'}", "{isSevere ? t`SEVERE HAZARD` : t`WARNING`}"),
    ("Forecast: ", "<Trans>Forecast: </Trans>"),
    ("Safe Limit: ", "<Trans>Safe Limit: </Trans>")
])

# HazardAlert.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/HazardAlert.tsx', [
    ("import { ShieldAlert, Clock, Database, Ruler } from 'lucide-react';", "import { ShieldAlert, Clock, Database, Ruler } from 'lucide-react';\nimport { Trans } from '@lingui/react/macro';"),
    ("Leg: {hazard.trip_phase}", "<Trans>Leg: {hazard.trip_phase}</Trans>"),
    ("Observed Forecast<", "Trans>Observed Forecast</Trans><"),
    (">Boat Safety Limit<", "><Trans>Boat Safety Limit</Trans><"),
    ("<span>Rule Applied: ", "<span><Trans>Rule Applied:</Trans> "),
    ("<span>Hazard Time: ", "<span><Trans>Hazard Time:</Trans> "),
    (" CONFIDENCE\n", " <Trans>CONFIDENCE</Trans>\n")
])

# ModificationModal.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/ModificationModal.tsx', [
    ("import { motion, AnimatePresence } from 'framer-motion';", "import { motion, AnimatePresence } from 'framer-motion';\nimport { Trans, useLingui } from '@lingui/react/macro';"),
    ("export const ModificationModal: React.FC<Props> = ({ isOpen, onClose }) => {", "export const ModificationModal: React.FC<Props> = ({ isOpen, onClose }) => {\n  const { t } = useLingui();"),
    ("const message = `Modify trip parameters: Departure at ${departureTime} from ${", "const message = t`Modify trip parameters: Departure at ${departureTime} from ${"),
    ("tripContext?.origin || 'Mangalore Port'", "tripContext?.origin || t`Mangalore Port`"),
    ("}, return earlier at ${effectiveReturn} IST to avoid return wave hazard.`;", "}, return earlier at ${effectiveReturn} IST to avoid return wave hazard.`;"),
    ("<span>Modify Voyage Timing & Route</span>", "<span><Trans>Modify Voyage Timing & Route</Trans></span>"),
    ("Suggested Mitigations:\n", "Trans>Suggested Mitigations:</Trans>\n"),
    ("Return at 12:00 PM", "<Trans>Return at 12:00 PM</Trans>"),
    ("Beat afternoon wave surge", "<Trans>Beat afternoon wave surge</Trans>"),
    ("Return at 1:00 PM", "<Trans>Return at 1:00 PM</Trans>"),
    ("Reduce return exposure", "<Trans>Reduce return exposure</Trans>"),
    ("<span>Custom Departure Time (IST):</span>", "<span><Trans>Custom Departure Time (IST):</Trans></span>"),
    ("<span>Custom Expected Return Time (IST):</span>", "<span><Trans>Custom Expected Return Time (IST):</Trans></span>"),
    ("Note: Changing return timing recalculates sea state wave heights for every waypoint along the return route.", "<Trans>Note: Changing return timing recalculates sea state wave heights for every waypoint along the return route.</Trans>"),
    (">Cancel<", "><Trans>Cancel</Trans><"),
    ("{loading ? 'Re-evaluating...' : 'Re-assess Voyage'}", "{loading ? t`Re-evaluating...` : t`Re-assess Voyage`}")
])

# RouteComparisonCard.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/RouteComparisonCard.tsx', [
    ("import { motion } from 'framer-motion';", "import { motion } from 'framer-motion';\nimport { Trans } from '@lingui/react/macro';"),
    ("Route Candidate Evaluation & Scoring", "<Trans>Route Candidate Evaluation & Scoring</Trans>"),
    ("{routeCandidates.length} Scored Trajectories", "<Trans>{routeCandidates.length} Scored Trajectories</Trans>"),
    ("SAGAR evaluates and scores candidate corridors against sea-state wave models, distance, and geofence boundaries:", "<Trans>SAGAR evaluates and scores candidate corridors against sea-state wave models, distance, and geofence boundaries:</Trans>"),
    ("Recommended\n", "<Trans>Recommended</Trans>\n"),
    (">Voyage Distance<", "><Trans>Voyage Distance</Trans><"),
    (">Est. Voyage Time<", "><Trans>Est. Voyage Time</Trans><"),
    (" Hours<", " <Trans>Hours</Trans><"),
    (">Weather Risk Penalty:<", "><Trans>Weather Risk Penalty:</Trans><"),
    (">Geofence Constraint:<", "><Trans>Geofence Constraint:</Trans><"),
    ("{route.penalty_breakdown.geofence_penalty > 0 ? 'Boundary Violation' : 'Clear'}", "{route.penalty_breakdown.geofence_penalty > 0 ? <Trans>Boundary Violation</Trans> : <Trans>Clear</Trans>}"),
    (" Corridor<", " <Trans>Corridor</Trans><"),
    ("<span>Active on Map</span>", "<span><Trans>Active on Map</Trans></span>"),
    ("<span>Click to Inspect</span>", "<span><Trans>Click to Inspect</Trans></span>")
])

# EvidencePanel.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/EvidencePanel.tsx', [
    ("import { motion, AnimatePresence } from 'framer-motion';", "import { motion, AnimatePresence } from 'framer-motion';\nimport { Trans } from '@lingui/react/macro';"),
    ('Data Evidence & Operational Provenance ("See Why")', '<Trans>Data Evidence & Operational Provenance ("See Why")</Trans>'),
    ("Verified dataset attribution, confidence ratings, and safety threshold triggers", "<Trans>Verified dataset attribution, confidence ratings, and safety threshold triggers</Trans>"),
    ("{triggersCount} Hazard Triggers\n", "<Trans>{triggersCount} Hazard Triggers</Trans>\n"),
    ("Hazard Triggers ({triggersCount})", "<Trans>Hazard Triggers ({triggersCount})</Trans>"),
    ("Evidence Registry ({registryCount})", "<Trans>Evidence Registry ({registryCount})</Trans>"),
    ("Attribution & Tiers", "<Trans>Attribution & Tiers</Trans>"),
    ("<span>No deterministic safety threshold violations were triggered across any leg of your trip.</span>", "<span><Trans>No deterministic safety threshold violations were triggered across any leg of your trip.</Trans></span>"),
    (" Agent<", " <Trans>Agent</Trans><"),
    ("Source: ", "<Trans>Source: </Trans>"),
    ("<span>Dataset Attribution & Fallback Tiers:</span>", "<span><Trans>Dataset Attribution & Fallback Tiers:</Trans></span>"),
    ("Valid: {prov.validity_time ? new Date(prov.validity_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : 'Current model cycle'}", "<Trans>Valid:</Trans> {prov.validity_time ? new Date(prov.validity_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : <Trans>Current model cycle</Trans>}"),
    ("{prov.fallback_tier === 1 ? 'Tier 1 Live' : prov.fallback_tier === 2 ? 'Tier 2 ML' : 'Tier 3 Ref'} • {prov.confidence}", "{prov.fallback_tier === 1 ? <Trans>Tier 1 Live</Trans> : prov.fallback_tier === 2 ? <Trans>Tier 2 ML</Trans> : <Trans>Tier 3 Ref</Trans>} • {prov.confidence}")
])

# RuleResultsPanel.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/RuleResultsPanel.tsx', [
    ("import { sanitizeSagarText } from '../../utils/brand';", "import { sanitizeSagarText } from '../../utils/brand';\nimport { Trans } from '@lingui/react/macro';"),
    ("Deterministic Stability & Safety Rules", "<Trans>Deterministic Stability & Safety Rules</Trans>"),
    ("{ruleResults.filter((r) => r.status === 'PASSED').length}/{ruleResults.length} Rules Passed", "<Trans>{ruleResults.filter((r) => r.status === 'PASSED').length}/{ruleResults.length} Rules Passed</Trans>")
])

# TripTimeline.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/TripTimeline.tsx', [
    ("import { motion } from 'framer-motion';", "import { motion } from 'framer-motion';\nimport { Trans, useLingui } from '@lingui/react/macro';"),
    ("export const TripTimeline: React.FC<Props> = ({ trajectory, hazardFlags = [] }) => {", "export const TripTimeline: React.FC<Props> = ({ trajectory, hazardFlags = [] }) => {\n  const { t } = useLingui();"),
    ("badge: 'SEVERE HAZARD',", "badge: t`SEVERE HAZARD`,"),
    ("label: `Wave ${hazard.observed_value}m > ${hazard.threshold_value}m limit`,", "label: t`Wave ${hazard.observed_value}m > ${hazard.threshold_value}m limit`,"),
    ("badge: 'MODERATE RISK',", "badge: t`MODERATE RISK`,"),
    ("label: 'Elevated wave swell',", "label: t`Elevated wave swell`,"),
    ("badge: 'SAFE',", "badge: t`SAFE`,"),
    ("label: 'Conditions within limits',", "label: t`Conditions within limits`,"),
    ("4D Voyage Journey Timeline", "<Trans>4D Voyage Journey Timeline</Trans>"),
    ("Click waypoints to focus map camera & ETA conditions", "<Trans>Click waypoints to focus map camera & ETA conditions</Trans>"),
    ("{trajectory.total_distance_km} km voyage\n", "<Trans>{trajectory.total_distance_km} km voyage</Trans>\n")
])

# AdvisoryBanner.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/AdvisoryBanner.tsx', [
    ("import { sanitizeSagarText } from '../../utils/brand';", "import { sanitizeSagarText } from '../../utils/brand';\nimport { useLingui } from '@lingui/react/macro';"),
    ("export const AdvisoryBanner: React.FC<Props> = ({ category, recommendationText }) => {", "export const AdvisoryBanner: React.FC<Props> = ({ category, recommendationText }) => {\n  const { t } = useLingui();"),
    ("title: 'SAFE — CONDITIONS FAVORABLE'", "title: t`SAFE — CONDITIONS FAVORABLE`"),
    ("title: 'MODERATE RISK — PROCEED WITH CAUTION'", "title: t`MODERATE RISK — PROCEED WITH CAUTION`"),
    ("title: 'HIGH RISK — ROUTE OR TIME MODIFICATION RECOMMENDED'", "title: t`HIGH RISK — ROUTE OR TIME MODIFICATION RECOMMENDED`"),
    ("title: 'SEVERE HAZARD DETECTED — VOYAGE NOT RECOMMENDED'", "title: t`SEVERE HAZARD DETECTED — VOYAGE NOT RECOMMENDED`"),
    ("title: 'INSUFFICIENT DATA — UNABLE TO SAFELY ASSESS VOYAGE'", "title: t`INSUFFICIENT DATA — UNABLE TO SAFELY ASSESS VOYAGE`")
])

# ConflictInfoCard.tsx
update_file('/home/flux/sagar/SAGAR/frontend/src/components/advisory/ConflictInfoCard.tsx', [
    ("import { sanitizeSagarText } from '../../utils/brand';", "import { sanitizeSagarText } from '../../utils/brand';\nimport { Trans } from '@lingui/react/macro';"),
    ("<span>Conflicting Data Sources Detected (Multi-Source Comparison)</span>", "<span><Trans>Conflicting Data Sources Detected (Multi-Source Comparison)</Trans></span>"),
    ("Different authoritative weather/marine models report divergent values for your voyage window. SAGAR presents both sources transparently without fabricating an ungrounded consensus:", "<Trans>Different authoritative weather/marine models report divergent values for your voyage window. SAGAR presents both sources transparently without fabricating an ungrounded consensus:</Trans>"),
    ("<span>Parameter: ", "<span><Trans>Parameter:</Trans> "),
    ("Source A: ", "<Trans>Source A:</Trans> "),
    ("Timestamp: ", "<Trans>Timestamp:</Trans> "),
    ("Source B: ", "<Trans>Source B:</Trans> ")
])

