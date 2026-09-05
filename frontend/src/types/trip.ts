export type TripPhase = 'OUTBOUND' | 'FISHING' | 'RETURN';
export type DestinationType = 'NEAREST_PFZ' | 'SPECIFIC_PFZ' | 'COORDINATES';

export interface Coordinates {
  lat: number;
  lon: number;
}

export interface TripContext {
  trip_id?: string;
  fisher_id?: string;
  vessel_id?: string;
  origin: string;
  origin_coordinates: Coordinates;
  destination_name?: string;
  destination_type: DestinationType;
  destination_coordinates: Coordinates;
  departure_time_iso: string;
  fishing_duration_hours: number;
  expected_return_time_iso: string;
  user_intent?: string;
}

export interface Waypoint {
  phase: TripPhase;
  lat: number;
  lon: number;
  eta_iso: string;
  name?: string;
}

export interface GeofenceIntersection {
  constraint_id: string;
  constraint_name: string;
  constraint_type: 'MPA' | 'INTERNATIONAL_BORDER' | 'NAVIGATIONAL_HAZARD' | 'MILITARY_ZONE';
  intersects: boolean;
  affected_waypoints: number[];
  source: string;
}

export interface Trajectory {
  route_id: string;
  total_distance_km: number;
  waypoints: Waypoint[];
  estimated_return_time_iso?: string;
  geofence_intersections?: GeofenceIntersection[];
}
