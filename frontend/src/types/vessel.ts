export interface VesselSafetyThresholds {
  max_safe_wave_m: number;
  rule_applied: string;
  formula?: string;
}

export interface VesselProfile {
  vessel_id: string;
  vessel_type: string;
  beam_width_m: number;
  length_m?: number;
  cruising_speed_kmh: number;
  has_ais?: boolean;
  registration_number?: string;
  home_port?: string;
  safety_thresholds?: VesselSafetyThresholds;
}
