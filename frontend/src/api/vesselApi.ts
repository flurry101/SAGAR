import { apiRequest } from './client';
import { APIResponse } from '../types/api';
import { VesselProfile } from '../types/vessel';

export const vesselApi = {
  getVesselProfile: (vesselId: string): Promise<APIResponse<VesselProfile>> => {
    return apiRequest(`/vessel/${vesselId}`, {
      method: 'GET',
    });
  },

  updateVesselProfile: (vesselId: string, profile: Partial<VesselProfile>): Promise<APIResponse<VesselProfile>> => {
    return apiRequest(`/vessel/${vesselId}`, {
      method: 'PUT',
      body: profile,
    });
  },
};
