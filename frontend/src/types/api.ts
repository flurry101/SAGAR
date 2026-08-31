import { TripContext, Trajectory, Waypoint } from './trip';
import { RiskEvidence, AlertItem, RuleResult, EvidenceItem, OverallRiskLevel } from './risk';
import { Advisory } from './advisory';
import { VesselProfile } from './vessel';

export type ResponseStatus = 'success' | 'needs_clarification' | 'insufficient_information' | 'error';

export interface MetaData {
  request_id?: string;
  timestamp: string;
  version: string;
  scenario_id?: string;
}

export interface MissingField {
  field: string;
  criticality: 'CRITICAL' | 'OPTIONAL';
  question: string;
}

export interface MissingDataItem {
  data_type: string;
  d_id?: string;
  reason: string;
  is_safety_critical: boolean;
}

export interface WeatherObservation {
  waypoint_index: number;
  lat: number;
  lon: number;
  time_iso: string;
  wave_height_m: number;
  wind_speed_kmh: number;
  wind_direction_deg: number;
  swell_height_m: number;
  visibility_km: number;
  stale?: boolean;
}

export interface MarineObservation {
  lat: number;
  lon: number;
  time_iso: string;
  sst_celsius: number;
  chlorophyll_mgm3: number;
  hab_detected: boolean;
  hab_probability: number;
  current_speed_kmh: number;
}

export interface PFZZone {
  pfz_id: string;
  coordinates: { lat: number; lon: number };
  valid_from: string;
  valid_until: string;
  distance_from_origin_km: number;
  available: boolean;
}

export interface RouteCandidatePenalty {
  weather_risk: number;
  geofence_penalty: number;
  hazard_penalty: number;
}

export interface RouteCandidate {
  route_id: string;
  route_type: 'primary' | 'coastal' | 'offshore';
  name: string;
  score: number;
  distance_nm: number;
  duration_hours: number;
  waypoints: Waypoint[];
  penalty_breakdown: RouteCandidatePenalty;
  is_recommended?: boolean;
}

export interface MapLayer {
  layer_id: string;
  type: 'line' | 'point' | 'polygon';
  geojson: any;
  style?: {
    color?: string;
    weight?: number;
    fillOpacity?: number;
    radius?: number;
  };
}

export interface VisualizationSpec {
  map_center: { lat: number; lon: number };
  zoom: number;
  layers: MapLayer[];
}

export interface OceanAnalysis {
  sst_celsius?: number;
  chlorophyll_mg_m3?: number;
  current_speed_knots?: number;
  pfz_status?: string;
}

export type TranslationProvider = 'bhashini' | 'gemini_fallback' | 'unavailable';

export interface AssessmentData {
  MOCK_WARNING?: string;
  trip_id?: string;
  session_id?: string;
  workflow_status: string;
  trip_context?: TripContext;
  trajectory?: Trajectory;
  risk_evidence?: RiskEvidence;
  advisory?: Advisory;
  advisory_category?: string;
  recommendation_text?: string;
  disclaimer?: string;
  missing_fields?: MissingField[];
  missing_data?: MissingDataItem[];
  understood_so_far?: Partial<TripContext>;
  overall_risk_level?: OverallRiskLevel;
  alerts?: AlertItem[];
  evidence_registry?: EvidenceItem[];
  route_candidates?: RouteCandidate[];
  visualization_spec?: VisualizationSpec;
  ocean_analysis?: OceanAnalysis;
  report?: any;
  vessel_profile?: VesselProfile;
  weather_forecasts?: WeatherObservation[];
  marine_observations?: MarineObservation[];
  pfz_zones?: PFZZone[];
  pfz_available?: boolean;
  language?: string;
  persistence_status?: 'success' | 'failed' | 'supabase_not_configured' | string;
  translation_provider?: TranslationProvider;
  errors?: string[];
  [key: string]: any;
}

export interface ClarificationData {
  session_id: string;
  workflow_status: 'CLARIFICATION_REQUIRED';
  missing_fields: MissingField[];
  understood_so_far: Partial<TripContext>;
}

export interface InsufficientInfoData {
  session_id: string;
  workflow_status: 'INSUFFICIENT_INFORMATION';
  advisory_category: 'INSUFFICIENT_INFORMATION';
  missing_data: MissingDataItem[];
  recommendation_text: string;
  disclaimer: string;
}

export interface ChatRequest {
  message: string;
  thread_id?: string;
  session_id?: string;
  language?: string;
  vessel_profile?: Partial<VesselProfile>;
}

export interface APIResponse<T = AssessmentData> {
  status: ResponseStatus;
  data?: T;
  error?: {
    code: string;
    message: string;
    details?: any;
  };
  meta?: MetaData;
}
