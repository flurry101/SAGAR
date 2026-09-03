import { apiRequest } from './client';
import { APIResponse, ChatRequest } from '../types/api';
import { normalizeAssessmentResponse } from './assessmentTransform';

export const tripApi = {
  async assessTrip(payload: ChatRequest | { message: string; session_id?: string; fisher_id?: string }): Promise<APIResponse> {
    const response = await apiRequest('/chat', {
      method: 'POST',
      body: payload,
    });
    return normalizeAssessmentResponse(response);
  },

  async continueTrip(payload: { session_id: string; message: string }): Promise<APIResponse> {
    const response = await apiRequest('/trip/continue', {
      method: 'POST',
      body: payload,
    });
    return normalizeAssessmentResponse(response);
  },

  async getAdvisory(tripId: string): Promise<APIResponse> {
    return apiRequest(`/trip/${tripId}/advisory`, {
      method: 'GET',
    });
  },
};
