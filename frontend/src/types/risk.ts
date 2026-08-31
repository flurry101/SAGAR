import { Coordinates } from './trip';
import { Provenance, ProvenanceSummary } from './provenance';

export type AdvisoryCategory =
  | 'CONDITIONS_FAVORABLE'
  | 'GO_WITH_CAUTION'
  | 'ELEVATED_RISK_IDENTIFIED'
  | 'CONSIDER_ROUTE_TIME_MODIFICATION'
  | 'SEVERE_HAZARD_OVERLAP'
  | 'INSUFFICIENT_INFORMATION';

export type OverallRiskLevel = 'SAFE' | 'MODERATE' | 'ELEVATED' | 'HIGH' | 'SEVERE' | 'UNKNOWN';

export type AlertSeverity = 'WARNING' | 'SEVERE';

export interface AlertItem {
  alert_type: string;
  severity: AlertSeverity;
  message: string;
  threshold?: number;
  actual_value?: number;
}

export interface RuleResult {
  rule_id: string;
  rule_name: string;
  status: 'PASSED' | 'FAILED';
  risk_level: OverallRiskLevel;
  details: string;
  evidence: Record<string, any>;
}

export interface EvidenceItem {
  evidence_id: string;
  category: string;
  value: number | string;
  unit?: string;
  source: string;
  timestamp: string;
  lat?: number;
  lon?: number;
  confidence: number | string;
  agent?: string;
}

export interface HazardFlag {
  trip_phase: 'OUTBOUND' | 'FISHING' | 'RETURN';
  hazard_type: string;
  waypoint_index: number;
  location: Coordinates;
  time_iso: string;
  observed_value: number;
  threshold_value: number;
  rule_applied: string;
  unit?: string;
  provenance: Provenance;
}

export interface DataConflict {
  variable: string;
  source_a: { name: string; value: string | number; timestamp: string };
  source_b: { name: string; value: string | number; timestamp: string };
  conflict_indicator: string;
}

export interface RiskEvidence {
  advisory_category: AdvisoryCategory;
  overall_risk_level: OverallRiskLevel;
  summary?: string;
  is_trip_recommended?: boolean;
  rule_results?: RuleResult[];
  hazard_flags: HazardFlag[];
  geofence_violations?: any[];
  data_conflicts?: DataConflict[];
  provenance_summary?: ProvenanceSummary[];
}
