import { APIResponse } from '../../types/api';
import { VesselProfile } from '../../types/vessel';
import { DEMO_SCENARIOS } from './scenarios';

export class MockAdapter {
  private activeScenarioId: string = 'SCENARIO_3_SEVERE_RETURN'; // Default to flagship 4D return hazard

  public setActiveScenario(scenarioId: string): void {
    if (DEMO_SCENARIOS[scenarioId]) {
      this.activeScenarioId = scenarioId;
    }
  }

  public getActiveScenarioId(): string {
    return this.activeScenarioId;
  }

  public async assessTrip(payload: { message: string; fisher_id?: string; session_id?: string }): Promise<APIResponse<any>> {
    await new Promise((resolve) => setTimeout(resolve, 600));

    // If message mentions missing info or beam
    if (payload.message.toLowerCase().includes('missing') || payload.message.toLowerCase().includes('no beam')) {
      return DEMO_SCENARIOS['SCENARIO_4_MISSING_INFO'].mockResponse;
    }

    const scenario = DEMO_SCENARIOS[this.activeScenarioId];
    return scenario ? scenario.mockResponse : DEMO_SCENARIOS['SCENARIO_3_SEVERE_RETURN'].mockResponse;
  }

  public async continueTrip(payload: { session_id: string; message: string }): Promise<APIResponse<any>> {
    await new Promise((resolve) => setTimeout(resolve, 500));
    return DEMO_SCENARIOS['SCENARIO_1_SAFE'].mockResponse;
  }

  public async getVesselProfile(vesselId: string): Promise<APIResponse<VesselProfile>> {
    await new Promise((resolve) => setTimeout(resolve, 250));
    return {
      status: 'success',
      data: {
        vessel_id: vesselId || 'vessel-trawler-45',
        vessel_type: 'Mechanized Trawler',
        beam_width_m: 4.5,
        length_m: 14.5,
        cruising_speed_kmh: 15.0,
        has_ais: true,
        registration_number: 'IND-KA-04-MM-8821',
        home_port: 'Mangalore Old Port',
        safety_thresholds: {
          max_safe_wave_m: 1.125,
          rule_applied: 'SVAS_CAPSIZE_BSI',
          formula: 'beam_width_m / 4.0'
        }
      }
    };
  }

  public async saveVesselProfile(vessel: any): Promise<APIResponse<VesselProfile>> {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const beam = parseFloat(vessel.beam_width_m) || 4.5;
    return {
      status: 'success',
      data: {
        ...vessel,
        beam_width_m: beam,
        safety_thresholds: {
          max_safe_wave_m: beam / 4.0,
          rule_applied: 'SVAS_CAPSIZE_BSI',
          formula: 'beam_width_m / 4.0'
        }
      }
    };
  }

  public async checkHealth(): Promise<APIResponse<any>> {
    await new Promise((resolve) => setTimeout(resolve, 100));
    return {
      status: 'success',
      data: {
        service: 'SAGAR-backend-mock',
        status: 'healthy',
        version: '1.0.0',
        decision_pipeline_ready: true,
        timestamp: new Date().toISOString()
      }
    };
  }
}

export const mockAdapter = new MockAdapter();
