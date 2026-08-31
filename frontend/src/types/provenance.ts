export type FallbackTier = 1 | 2 | 3;
export type ConfidenceLevel = 'HIGH' | 'MODERATE' | 'LOW';

export interface Provenance {
  source: string;
  retrieved_at: string;
  validity_time?: string;
  fallback_tier: FallbackTier;
  confidence: ConfidenceLevel;
}

export interface ProvenanceSummary {
  source: string;
  retrieved_at?: string;
  validity_time?: string;
  fallback_tier: FallbackTier;
  confidence: ConfidenceLevel;
}
