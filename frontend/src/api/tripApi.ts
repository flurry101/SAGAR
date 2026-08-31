import { apiRequest } from './client';
import { APIResponse, ChatRequest } from '../types/api';

export const tripApi = {
  async assessTrip(payload: ChatRequest | { message: string; session_id?: string; fisher_id?: string }): Promise<APIResponse> {
    return apiRequest('/chat', {
      method: 'POST',
      body: payload,
    });
  },

  async continueTrip(payload: { session_id: string; message: string }): Promise<APIResponse> {
    return apiRequest('/trip/continue', {
      method: 'POST',
      body: payload,
    });
  },

  async getAdvisory(tripId: string): Promise<APIResponse> {
    return apiRequest(`/trip/${tripId}/advisory`, {
      method: 'GET',
    });
  },
};
