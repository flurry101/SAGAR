import { apiRequest } from './client';

export interface UserCreatePayload {
  name?: string;
  preferred_language?: string;
  home_port?: string;
  vessel_id?: string;
}

export interface UserUpdatePayload {
  name?: string;
  preferred_language?: string;
  home_port?: string;
  vessel_id?: string;
}

export const userApi = {
  async createUser(payload?: UserCreatePayload) {
    return apiRequest('/user/create', {
      method: 'POST',
      body: payload,
    });
  },

  async getCurrentUser() {
    return apiRequest('/user/me', {
      method: 'GET',
    });
  },

  async updateCurrentUser(payload: UserUpdatePayload) {
    return apiRequest('/user/me', {
      method: 'PUT',
      body: payload,
    });
  },

  async getTokenInfo() {
    return apiRequest('/user/token-info', {
      method: 'GET',
    });
  },
};
