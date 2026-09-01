import { APIResponse } from '../types/api';
import { mockAdapter } from './mock/mockAdapter';
import { getSupabaseAccessToken } from './supabaseClient';
import { useAppStore } from '../state/appStore';

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1';
const USE_MOCK = import.meta.env.VITE_USE_MOCK_API !== 'false';

export async function apiRequest<T = any>(
  endpoint: string,
  options: {
    method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
    body?: any;
    headers?: Record<string, string>;
  } = {}
): Promise<APIResponse<T>> {
  const { method = 'GET', body, headers = {} } = options;

  if (USE_MOCK) {
    // Intercept with Mock Adapter for development/demo safety
    if ((endpoint === '/chat' || endpoint === '/trip/assess') && method === 'POST') {
      const res = await mockAdapter.assessTrip(body);
      return res as unknown as APIResponse<T>;
    }
    if ((endpoint === '/trip/continue' || endpoint === '/copilot') && method === 'POST') {
      const res = await mockAdapter.continueTrip(body);
      return res as unknown as APIResponse<T>;
    }
    if (endpoint.startsWith('/vessel/') && method === 'GET') {
      const vesselId = endpoint.split('/vessel/')[1];
      const res = await mockAdapter.getVesselProfile(vesselId);
      return res as unknown as APIResponse<T>;
    }
    if (endpoint.startsWith('/vessel/') && method === 'PUT') {
      const res = await mockAdapter.saveVesselProfile(body);
      return res as unknown as APIResponse<T>;
    }
    if (endpoint === '/user/me' && method === 'GET') {
      const store = useAppStore.getState();
      if (!store.isAuthenticated || !store.userProfile) {
        return {
          status: 'error',
          error: {
            code: 'UNAUTHENTICATED',
            message: 'Authentication required to access the current user profile.',
          },
        } as APIResponse<T>;
      }

      const user = store.userProfile;
      return {
        status: 'success',
        data: {
          user_id: user.userId || 'user-demo-001',
          name: user.name,
          home_port: user.port,
          email: user.email || '',
          preferred_language: store.selectedLanguage,
        } as unknown as T,
      };
    }
    if (endpoint === '/user/create' && method === 'POST') {
      const store = useAppStore.getState();
      if (!store.isAuthenticated) {
        return {
          status: 'error',
          error: {
            code: 'UNAUTHENTICATED',
            message: 'Authentication required to create a user profile.',
          },
        } as APIResponse<T>;
      }

      return {
        status: 'success',
        data: {
          message: 'User created successfully',
          user_id: store.userProfile?.userId || 'user-demo-001',
          supabase_uid: 'supa-demo-uid',
          ...body,
        } as unknown as T,
      };
    }
    if (endpoint === '/health' || endpoint === '/ready') {
      const res = await mockAdapter.checkHealth();
      return res as unknown as APIResponse<T>;
    }
  }

  // Retrieve Supabase JWT Token for backend authorization
  let authToken = await getSupabaseAccessToken();
  if (!authToken) {
    authToken = useAppStore.getState().supabaseToken;
  }

  const authHeaders: Record<string, string> = {};
  if (authToken) {
    authHeaders['Authorization'] = `Bearer ${authToken}`;
  }

  // HTTP Fetch Call to FastAPI
  try {
    const res = await fetch(`${API_BASE_URL}${endpoint}`, {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...authHeaders,
        ...headers,
      },
      body: body ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      return {
        status: 'error',
        error: {
          code: errorData.code || `HTTP_${res.status}`,
          message: errorData.detail || errorData.message || 'Server request failed',
          details: errorData.details,
        },
      };
    }

    return await res.json();
  } catch (err: any) {
    return {
      status: 'error',
      error: {
        code: 'NETWORK_ERROR',
        message: 'Unable to connect to SAGAR decision-support service. Please verify your connection or backend server.',
        details: err.message,
      },
    };
  }
}
