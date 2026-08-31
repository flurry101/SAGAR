import { apiRequest } from './client';
import { APIResponse } from '../types/api';

export const healthApi = {
  checkHealth: (): Promise<APIResponse> => {
    return apiRequest('/health', {
      method: 'GET',
    });
  },
  checkReadiness: (): Promise<APIResponse> => {
    return apiRequest('/ready', {
      method: 'GET',
    });
  },
};
