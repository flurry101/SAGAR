import { AdvisoryCategory } from './risk';

export interface Advisory {
  advisory_category: AdvisoryCategory;
  recommendation_text: string;
  reason: string;
  affected_phase?: string;
  affected_time?: string;
  affected_location?: string;
  vessel_context?: string;
  evidence_summary?: string;
  uncertainty_notes?: string;
  disclaimer: string;
  language?: string;
}
