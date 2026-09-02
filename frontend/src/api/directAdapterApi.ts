import { apiRequest } from './client';
import { APIResponse } from '../types/api';

export type Coordinate = { lat: number; lon: number };

export type AdapterProvenance = {
  source?: string | null;
  retrieved_at?: string | null;
  validity_time?: string | null;
  fallback_tier?: 1 | 2 | 3;
  confidence?: string | null;
};

export type DirectAdapterResponse = APIResponse<Record<string, any>>;

/** Direct M4 adapter calls. These deliberately bypass chat, trip assessment, and graph routes. */
export const directAdapterApi = {
  weatherForecast(coordinate: Coordinate, etaIso: string): Promise<DirectAdapterResponse> {
    return apiRequest('/weather/forecast', {
      method: 'POST',
      body: { waypoints: [{ ...coordinate, eta_iso: etaIso }] },
    });
  },

  weatherHazards(coordinate: Coordinate): Promise<DirectAdapterResponse> {
    const padding = 0.35;
    return apiRequest('/weather/hazards', {
      method: 'POST',
      body: {
        bbox: {
          lat_min: coordinate.lat - padding,
          lat_max: coordinate.lat + padding,
          lon_min: coordinate.lon - padding,
          lon_max: coordinate.lon + padding,
        },
      },
    });
  },

  potentialFishingZones(coordinate: Coordinate, radiusKm = 100): Promise<DirectAdapterResponse> {
    return apiRequest('/marine/pfz', {
      method: 'POST',
      body: { origin: coordinate, radius_km: radiusKm },
    });
  },

  marineObservations(coordinate: Coordinate, etaIso: string): Promise<DirectAdapterResponse> {
    return apiRequest('/marine/observations', {
      method: 'POST',
      body: { waypoints: [{ ...coordinate, eta_iso: etaIso }] },
    });
  },

  tides(coordinate: Coordinate, etaIso: string): Promise<DirectAdapterResponse> {
    return apiRequest('/marine/tides', {
      method: 'POST',
      body: { waypoints: [{ ...coordinate, eta_iso: etaIso }] },
    });
  },

  bathymetry(coordinate: Coordinate): Promise<DirectAdapterResponse> {
    return apiRequest('/marine/bathymetry', {
      method: 'POST',
      body: { waypoints: [{ ...coordinate }] },
    });
  },
};
