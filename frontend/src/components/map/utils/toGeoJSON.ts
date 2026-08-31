import { Waypoint, Coordinates, GeofenceIntersection } from '../../../types/trip';
import { HazardFlag } from '../../../types/risk';
import { PFZZone } from '../../../types/api';

export function waypointsToGeoJSONLine(waypoints: Waypoint[]) {
  return {
    type: 'Feature' as const,
    properties: {},
    geometry: {
      type: 'LineString' as const,
      coordinates: waypoints.map((wp) => [wp.lon, wp.lat]),
    },
  };
}

export function waypointsToGeoJSONPoints(waypoints: Waypoint[]) {
  return {
    type: 'FeatureCollection' as const,
    features: waypoints.map((wp, idx) => ({
      type: 'Feature' as const,
      properties: {
        index: idx + 1,
        phase: wp.phase,
        eta: wp.eta_iso,
        name: wp.name || `Waypoint ${idx + 1}`,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [wp.lon, wp.lat],
      },
    })),
  };
}

export function pfzToGeoJSON(pfzZones: PFZZone[]) {
  return {
    type: 'FeatureCollection' as const,
    features: pfzZones.map((pfz) => ({
      type: 'Feature' as const,
      properties: {
        pfz_id: pfz.pfz_id,
        distance_km: pfz.distance_from_origin_km,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [pfz.coordinates.lon, pfz.coordinates.lat],
      },
    })),
  };
}

export function hazardsToGeoJSON(hazardFlags: HazardFlag[]) {
  return {
    type: 'FeatureCollection' as const,
    features: hazardFlags.map((h, idx) => ({
      type: 'Feature' as const,
      properties: {
        type: h.hazard_type,
        observed: h.observed_value,
        threshold: h.threshold_value,
        phase: h.trip_phase,
      },
      geometry: {
        type: 'Point' as const,
        coordinates: [h.location.lon, h.location.lat],
      },
    })),
  };
}
