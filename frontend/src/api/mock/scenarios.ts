import { APIResponse } from '../../types/api';

export interface DemoScenario {
  id: string;
  name: string;
  badge: string;
  description: string;
  mockResponse: APIResponse;
}

export const DEMO_SCENARIOS: Record<string, DemoScenario> = {
  'SCENARIO_1_SAFE': {
    id: 'SCENARIO_1_SAFE',
    name: '1. Conditions Favourable',
    badge: '🟢 SAFE TRIP',
    description: 'Full safe trip across outbound, fishing, and return phases.',
    mockResponse: {
      status: 'success',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        trip_id: 'trip-scenario-1',
        session_id: 'sess-safe-001',
        workflow_status: 'COMPLETED',
        persistence_status: 'success',
        translation_provider: 'bhashini',
        language: 'en',
        overall_risk_level: 'SAFE',
        trip_context: {
          origin: 'Mangalore Port',
          origin_coordinates: { lat: 12.87, lon: 74.84 },
          destination_type: 'NEAREST_PFZ',
          destination_coordinates: { lat: 12.75, lon: 74.50 },
          departure_time_iso: '2026-08-30T05:00:00+05:30',
          fishing_duration_hours: 3.0,
          expected_return_time_iso: '2026-08-30T14:00:00+05:30'
        },
        trajectory: {
          route_id: 'ROUTE-SAFE-01',
          total_distance_km: 84.0,
          waypoints: [
            { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: 'Mangalore Departure' },
            { phase: 'OUTBOUND', lat: 12.81, lon: 74.68, eta_iso: '2026-08-30T06:30:00+05:30', name: 'Coastal Transit' },
            { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T08:00:00+05:30', name: 'Mangalore South PFZ' },
            { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T11:00:00+05:30', name: 'PFZ Operations End' },
            { phase: 'RETURN', lat: 12.81, lon: 74.68, eta_iso: '2026-08-30T12:30:00+05:30', name: 'Return Transit' },
            { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T14:00:00+05:30', name: 'Harbor Arrival' }
          ],
          geofence_intersections: []
        },
        alerts: [],
        route_candidates: [
          {
            route_id: 'route-primary-01',
            route_type: 'primary',
            name: 'Primary Direct Route',
            score: 94.5,
            distance_nm: 45.3,
            duration_hours: 9.0,
            is_recommended: true,
            waypoints: [
              { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: 'Mangalore Departure' },
              { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T08:00:00+05:30', name: 'Mangalore South PFZ' },
              { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T14:00:00+05:30', name: 'Harbor Arrival' }
            ],
            penalty_breakdown: { weather_risk: 0.05, geofence_penalty: 0.0, hazard_penalty: 0.0 }
          },
          {
            route_id: 'route-coastal-01',
            route_type: 'coastal',
            name: 'Inshore Coastal Bypass',
            score: 88.0,
            distance_nm: 51.2,
            duration_hours: 10.0,
            is_recommended: false,
            waypoints: [
              { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: 'Mangalore Departure' },
              { phase: 'OUTBOUND', lat: 12.80, lon: 74.78, eta_iso: '2026-08-30T06:45:00+05:30', name: 'Inshore Channel' },
              { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T08:30:00+05:30', name: 'Mangalore South PFZ' },
              { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T15:00:00+05:30', name: 'Harbor Arrival' }
            ],
            penalty_breakdown: { weather_risk: 0.08, geofence_penalty: 0.0, hazard_penalty: 0.0 }
          }
        ],
        visualization_spec: {
          map_center: { lat: 12.81, lon: 74.67 },
          zoom: 10,
          layers: [
            {
              layer_id: 'trajectory',
              type: 'line',
              geojson: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: [
                    [74.84, 12.87],
                    [74.68, 12.81],
                    [74.50, 12.75],
                    [74.68, 12.81],
                    [74.84, 12.87]
                  ]
                }
              },
              style: { color: '#0284c7', weight: 4 }
            },
            {
              layer_id: 'pfz_zones',
              type: 'point',
              geojson: {
                type: 'FeatureCollection',
                features: [
                  {
                    type: 'Feature',
                    properties: { name: 'Mangalore South PFZ' },
                    geometry: { type: 'Point', coordinates: [74.50, 12.75] }
                  }
                ]
              },
              style: { color: '#10b981', radius: 10 }
            }
          ]
        },
        risk_evidence: {
          advisory_category: 'CONDITIONS_FAVORABLE',
          overall_risk_level: 'SAFE',
          summary: 'All physical ocean and meteorological parameters are within vessel tolerance.',
          is_trip_recommended: true,
          rule_results: [
            {
              rule_id: 'RULE_SVAS_CAPSIZE_01',
              rule_name: 'SVAS Small Vessel Stability Limit',
              status: 'PASSED',
              risk_level: 'SAFE',
              details: 'Max forecast wave height (0.85m) is within vessel safety limit (1.125m).',
              evidence: { svas_ratio: 0.188, svas_limit: 0.25, max_wave_m: 0.85, vessel_beam_m: 4.5 }
            },
            {
              rule_id: 'RULE_WIND_GUST_01',
              rule_name: 'Coastal Wind Gust Limit',
              status: 'PASSED',
              risk_level: 'SAFE',
              details: 'Max wind speed 14 km/h is below warning threshold (40 km/h).',
              evidence: { max_wind_kmh: 14.0, limit_kmh: 40.0 }
            },
            {
              rule_id: 'RULE_GEOFENCE_01',
              rule_name: 'Marine Protected Area Boundary Check',
              status: 'PASSED',
              risk_level: 'SAFE',
              details: 'Trajectory has zero intersections with restricted MPA polygons.',
              evidence: { violations_count: 0 }
            }
          ],
          hazard_flags: [],
          provenance_summary: [
            { source: 'Open-Meteo Marine API (ECMWF IFS)', fallback_tier: 1, confidence: 'HIGH' },
            { source: 'INCOIS PFZ GeoJSON (Oceansat-3)', fallback_tier: 1, confidence: 'HIGH' }
          ]
        },
        evidence_registry: [
          { evidence_id: 'ev-wave-01', category: 'weather', value: 0.85, unit: 'm', source: 'Open-Meteo Marine', timestamp: '2026-08-30T04:30:00Z', confidence: 0.95, agent: 'weather' },
          { evidence_id: 'ev-wind-01', category: 'weather', value: 14.0, unit: 'km/h', source: 'Open-Meteo High-Res', timestamp: '2026-08-30T04:30:00Z', confidence: 0.95, agent: 'weather' },
          { evidence_id: 'ev-sst-01', category: 'marine', value: 28.5, unit: '°C', source: 'INCOIS Satellite SST', timestamp: '2026-08-30T03:00:00Z', confidence: 0.90, agent: 'marine' }
        ],
        ocean_analysis: {
          sst_celsius: 28.5,
          chlorophyll_mg_m3: 1.8,
          current_speed_knots: 0.6,
          pfz_status: 'ACTIVE_AGGREGATION_IDENTIFIED'
        },
        advisory: {
          advisory_category: 'CONDITIONS_FAVORABLE',
          recommendation_text: 'Sea conditions and weather are favourable for your planned trip to Mangalore South PFZ. Expected wave heights remain under 0.9m throughout your journey.',
          reason: 'All wave, wind, and swell forecasts are safely below vessel threshold (1.125m)',
          vessel_context: 'Mechanized Trawler (4.5m beam) → Max Safe Wave: 1.125m (SVAS standard). Expected max wave: 0.85m.',
          evidence_summary: 'Live marine forecast from Open-Meteo API (Tier 1, High Confidence).',
          disclaimer: 'SAGAR provides decision support only. Follow official alerts from INCOIS and IMD. The skipper retains ultimate operational command.',
          language: 'en'
        },
        vessel_profile: {
          vessel_id: 'vessel-trawler-45',
          vessel_type: 'Mechanized Trawler',
          beam_width_m: 4.5,
          length_m: 14.2,
          cruising_speed_kmh: 15.0,
          safety_thresholds: {
            max_safe_wave_m: 1.125,
            rule_applied: 'SVAS_CAPSIZE_BSI'
          }
        },
        weather_forecasts: [
          { waypoint_index: 0, lat: 12.87, lon: 74.84, time_iso: '2026-08-30T05:00:00+05:30', wave_height_m: 0.6, wind_speed_kmh: 10, wind_direction_deg: 210, swell_height_m: 0.4, visibility_km: 12 },
          { waypoint_index: 2, lat: 12.75, lon: 74.50, time_iso: '2026-08-30T08:00:00+05:30', wave_height_m: 0.8, wind_speed_kmh: 12, wind_direction_deg: 220, swell_height_m: 0.5, visibility_km: 10 },
          { waypoint_index: 5, lat: 12.87, lon: 74.84, time_iso: '2026-08-30T14:00:00+05:30', wave_height_m: 0.85, wind_speed_kmh: 14, wind_direction_deg: 230, swell_height_m: 0.5, visibility_km: 10 }
        ],
        pfz_available: true,
        pfz_zones: [
          { pfz_id: 'PFZ-KAR-001', coordinates: { lat: 12.75, lon: 74.50 }, valid_from: '2026-08-30T00:00:00+05:30', valid_until: '2026-08-31T00:00:00+05:30', distance_from_origin_km: 42.0, available: true }
        ],
        errors: []
      },
      meta: { request_id: 'req-safe-001', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_1_SAFE' }
    }
  },

  'SCENARIO_2_ELEVATED': {
    id: 'SCENARIO_2_ELEVATED',
    name: '2. Elevated Risk Identified',
    badge: '🟡 ELEVATED RISK',
    description: 'Elevated wave/wind conditions during fishing phase requiring caution.',
    mockResponse: {
      status: 'success',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        trip_id: 'trip-scenario-2',
        session_id: 'sess-elevated-002',
        workflow_status: 'COMPLETED',
        persistence_status: 'success',
        translation_provider: 'bhashini',
        language: 'en',
        overall_risk_level: 'MODERATE',
        trip_context: {
          origin: 'Malpe Harbor',
          origin_coordinates: { lat: 13.35, lon: 74.70 },
          destination_type: 'NEAREST_PFZ',
          destination_coordinates: { lat: 13.20, lon: 74.30 },
          departure_time_iso: '2026-08-30T06:00:00+05:30',
          fishing_duration_hours: 4.0,
          expected_return_time_iso: '2026-08-30T16:00:00+05:30'
        },
        trajectory: {
          route_id: 'ROUTE-ELEV-02',
          total_distance_km: 96.0,
          waypoints: [
            { phase: 'OUTBOUND', lat: 13.35, lon: 74.70, eta_iso: '2026-08-30T06:00:00+05:30', name: 'Malpe Departure' },
            { phase: 'FISHING', lat: 13.20, lon: 74.30, eta_iso: '2026-08-30T09:00:00+05:30', name: 'Offshore Fishing Zone' },
            { phase: 'FISHING', lat: 13.20, lon: 74.30, eta_iso: '2026-08-30T13:00:00+05:30', name: 'High Wind Window' },
            { phase: 'RETURN', lat: 13.35, lon: 74.70, eta_iso: '2026-08-30T16:00:00+05:30', name: 'Malpe Arrival' }
          ],
          geofence_intersections: []
        },
        alerts: [
          { alert_type: 'STRONG_WIND', severity: 'WARNING', message: 'Wind gusts reaching 28.5 km/h exceed comfortable handling limit during midday fishing.', threshold: 25.0, actual_value: 28.5 }
        ],
        route_candidates: [
          {
            route_id: 'route-malpe-01',
            route_type: 'primary',
            name: 'Direct Offshore Course',
            score: 76.0,
            distance_nm: 51.8,
            duration_hours: 10.0,
            is_recommended: true,
            waypoints: [
              { phase: 'OUTBOUND', lat: 13.35, lon: 74.70, eta_iso: '2026-08-30T06:00:00+05:30', name: 'Malpe Departure' },
              { phase: 'FISHING', lat: 13.20, lon: 74.30, eta_iso: '2026-08-30T09:00:00+05:30', name: 'Offshore Fishing Zone' },
              { phase: 'RETURN', lat: 13.35, lon: 74.70, eta_iso: '2026-08-30T16:00:00+05:30', name: 'Malpe Arrival' }
            ],
            penalty_breakdown: { weather_risk: 0.24, geofence_penalty: 0.0, hazard_penalty: 0.0 }
          }
        ],
        visualization_spec: {
          map_center: { lat: 13.28, lon: 74.50 },
          zoom: 10,
          layers: [
            {
              layer_id: 'trajectory',
              type: 'line',
              geojson: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: [
                    [74.70, 13.35],
                    [74.30, 13.20],
                    [74.70, 13.35]
                  ]
                }
              },
              style: { color: '#eab308', weight: 4 }
            }
          ]
        },
        risk_evidence: {
          advisory_category: 'ELEVATED_RISK_IDENTIFIED',
          overall_risk_level: 'MODERATE',
          summary: 'Midday wind gusts elevate wave action. Monitor local sea state closely.',
          is_trip_recommended: true,
          rule_results: [
            {
              rule_id: 'RULE_WIND_GUST_01',
              rule_name: 'Wind Gust Limit Check',
              status: 'FAILED',
              risk_level: 'MODERATE',
              details: 'Wind gust 28.5 km/h exceeds 25.0 km/h advisory limit for small motorized craft.',
              evidence: { max_wind_kmh: 28.5, limit_kmh: 25.0 }
            }
          ],
          hazard_flags: [
            {
              trip_phase: 'FISHING',
              hazard_type: 'WIND_GUST_ELEVATED',
              waypoint_index: 2,
              location: { lat: 13.20, lon: 74.30 },
              time_iso: '2026-08-30T13:00:00+05:30',
              observed_value: 28.5,
              threshold_value: 25.0,
              rule_applied: 'WIND_GUST_SAFETY_LIMIT',
              unit: 'km/h',
              provenance: { source: 'Open-Meteo High-Res API', retrieved_at: new Date().toISOString(), fallback_tier: 1, confidence: 'HIGH' }
            }
          ],
          provenance_summary: [
            { source: 'Open-Meteo High-Res API', fallback_tier: 1, confidence: 'HIGH' }
          ]
        },
        evidence_registry: [
          { evidence_id: 'ev-wind-elev-01', category: 'weather', value: 28.5, unit: 'km/h', source: 'Open-Meteo High-Res', timestamp: '2026-08-30T04:30:00Z', confidence: 0.90, agent: 'weather' }
        ],
        advisory: {
          advisory_category: 'ELEVATED_RISK_IDENTIFIED',
          recommendation_text: 'Elevated wind gusts (28.5 km/h) are expected around 1:00 PM in the fishing zone. Proceed with caution and keep your VHF radio monitored.',
          reason: 'Wind speed exceeds 25 km/h limit during midday fishing operations',
          affected_phase: 'FISHING',
          affected_time: '2026-08-30T13:00:00+05:30',
          affected_location: 'Offshore Malpe (13.20°N, 74.30°E)',
          vessel_context: 'Motorized Fibre Boat (2.8m beam) → Wind limit 25 km/h.',
          evidence_summary: 'Wind speed spike predicted at 13:00 IST by Open-Meteo API.',
          disclaimer: 'SAGAR provides decision support only. Follow official alerts from INCOIS and IMD.',
          language: 'en'
        },
        vessel_profile: {
          vessel_id: 'vessel-fibre-28',
          vessel_type: 'Motorized Fibre Craft',
          beam_width_m: 2.8,
          cruising_speed_kmh: 18.0
        },
        errors: []
      },
      meta: { request_id: 'req-elevated-002', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_2_ELEVATED' }
    }
  },

  'SCENARIO_3_SEVERE_RETURN': {
    id: 'SCENARIO_3_SEVERE_RETURN',
    name: '3. Severe Return Hazard (Flagship 4D)',
    badge: '🔴 SEVERE HAZARD',
    description: 'Safe departure & fishing ground, but severe capsize wave hazard during return at 4:00 PM.',
    mockResponse: {
      status: 'success',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        trip_id: 'trip-scenario-3',
        session_id: 'sess-severe-003',
        workflow_status: 'COMPLETED',
        persistence_status: 'success',
        translation_provider: 'bhashini',
        language: 'en',
        overall_risk_level: 'SEVERE',
        trip_context: {
          origin: 'Mangalore Old Port',
          origin_coordinates: { lat: 12.87, lon: 74.84 },
          destination_type: 'NEAREST_PFZ',
          destination_coordinates: { lat: 12.75, lon: 74.50 },
          departure_time_iso: '2026-08-30T05:00:00+05:30',
          fishing_duration_hours: 5.0,
          expected_return_time_iso: '2026-08-30T18:00:00+05:30'
        },
        trajectory: {
          route_id: 'ROUTE-FLAGSHIP-03',
          total_distance_km: 110.0,
          waypoints: [
            { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: '05:00 Departure (Safe 0.7m)' },
            { phase: 'OUTBOUND', lat: 12.80, lon: 74.70, eta_iso: '2026-08-30T07:00:00+05:30', name: '07:00 Transit (Safe 0.8m)' },
            { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T10:00:00+05:30', name: '10:00 Fishing (Safe 0.9m)' },
            { phase: 'RETURN', lat: 12.80, lon: 74.70, eta_iso: '2026-08-30T16:00:00+05:30', name: '16:00 Return Leg (SEVERE HAZARD 2.8m)' },
            { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T18:00:00+05:30', name: '18:00 Harbor Arrival (2.5m)' }
          ],
          geofence_intersections: []
        },
        alerts: [
          {
            alert_type: 'EXTREME_WAVE',
            severity: 'SEVERE',
            message: 'Significant wave height 2.8m exceeds 1.125m capsize safety threshold during return transit at 16:00 IST.',
            threshold: 1.125,
            actual_value: 2.8
          },
          {
            alert_type: 'STRONG_WIND',
            severity: 'WARNING',
            message: 'Afternoon coastal squall wind reaching 38 km/h along return corridor.',
            threshold: 30.0,
            actual_value: 38.0
          }
        ],
        route_candidates: [
          {
            route_id: 'route-standard-return',
            route_type: 'primary',
            name: 'Standard Return Path (Unsafe)',
            score: 32.0,
            distance_nm: 59.4,
            duration_hours: 13.0,
            is_recommended: false,
            waypoints: [
              { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: '05:00 Departure' },
              { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T10:00:00+05:30', name: '10:00 Fishing' },
              { phase: 'RETURN', lat: 12.80, lon: 74.70, eta_iso: '2026-08-30T16:00:00+05:30', name: '16:00 Wave Hazard Zone' },
              { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T18:00:00+05:30', name: '18:00 Arrival' }
            ],
            penalty_breakdown: { weather_risk: 0.68, geofence_penalty: 0.0, hazard_penalty: 0.0 }
          },
          {
            route_id: 'route-early-return',
            route_type: 'coastal',
            name: 'Suggested Modification: Return by 13:00 IST',
            score: 91.0,
            distance_nm: 52.0,
            duration_hours: 8.0,
            is_recommended: true,
            waypoints: [
              { phase: 'OUTBOUND', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T05:00:00+05:30', name: '05:00 Departure' },
              { phase: 'FISHING', lat: 12.75, lon: 74.50, eta_iso: '2026-08-30T08:00:00+05:30', name: '08:00 Fishing (Shortened)' },
              { phase: 'RETURN', lat: 12.80, lon: 74.70, eta_iso: '2026-08-30T11:30:00+05:30', name: '11:30 Safe Return' },
              { phase: 'RETURN', lat: 12.87, lon: 74.84, eta_iso: '2026-08-30T13:00:00+05:30', name: '13:00 Safe Arrival (0.8m)' }
            ],
            penalty_breakdown: { weather_risk: 0.09, geofence_penalty: 0.0, hazard_penalty: 0.0 }
          }
        ],
        visualization_spec: {
          map_center: { lat: 12.81, lon: 74.67 },
          zoom: 10,
          layers: [
            {
              layer_id: 'trajectory',
              type: 'line',
              geojson: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: [
                    [74.84, 12.87],
                    [74.70, 12.80],
                    [74.50, 12.75],
                    [74.70, 12.80],
                    [74.84, 12.87]
                  ]
                }
              },
              style: { color: '#ef4444', weight: 4 }
            },
            {
              layer_id: 'hazard_zones',
              type: 'polygon',
              geojson: {
                type: 'Feature',
                properties: { name: 'Afternoon Wave Surge Corridor (2.8m)' },
                geometry: {
                  type: 'Polygon',
                  coordinates: [[
                    [74.62, 12.75],
                    [74.78, 12.75],
                    [74.78, 12.85],
                    [74.62, 12.85],
                    [74.62, 12.75]
                  ]]
                }
              },
              style: { color: '#f87171', fillOpacity: 0.3 }
            }
          ]
        },
        risk_evidence: {
          advisory_category: 'SEVERE_HAZARD_OVERLAP',
          overall_risk_level: 'SEVERE',
          summary: 'Critical wave height surge (2.8m) projected during return transit between 15:30 and 18:00 IST.',
          is_trip_recommended: false,
          rule_results: [
            {
              rule_id: 'RULE_SVAS_CAPSIZE_01',
              rule_name: 'SVAS Small Vessel Stability Limit',
              status: 'FAILED',
              risk_level: 'SEVERE',
              details: 'Wave height forecast (2.8m) exceeds safe capsize limit (1.125m) by 148% during return leg.',
              evidence: { svas_ratio: 0.622, svas_limit: 0.25, max_wave_m: 2.8, vessel_beam_m: 4.5 }
            },
            {
              rule_id: 'RULE_WIND_GUST_01',
              rule_name: 'Coastal Squall Wind Limit',
              status: 'FAILED',
              risk_level: 'MODERATE',
              details: 'Wind speed (38 km/h) exceeds safe operating limit (30 km/h) at 16:00 IST.',
              evidence: { max_wind_kmh: 38.0, limit_kmh: 30.0 }
            }
          ],
          hazard_flags: [
            {
              trip_phase: 'RETURN',
              hazard_type: 'WAVE_HEIGHT_EXCEEDED',
              waypoint_index: 3,
              location: { lat: 12.80, lon: 74.70 },
              time_iso: '2026-08-30T16:00:00+05:30',
              observed_value: 2.8,
              threshold_value: 1.125,
              rule_applied: 'SVAS_CAPSIZE_BSI',
              unit: 'm',
              provenance: {
                source: 'Open-Meteo Marine API',
                retrieved_at: '2026-08-30T04:30:00Z',
                validity_time: '2026-08-30T16:00:00+05:30',
                fallback_tier: 1,
                confidence: 'HIGH'
              }
            }
          ],
          provenance_summary: [
            { source: 'Open-Meteo Marine API', fallback_tier: 1, confidence: 'HIGH' },
            { source: 'INCOIS PFZ Reference (Oceansat-3)', fallback_tier: 1, confidence: 'HIGH' }
          ]
        },
        evidence_registry: [
          { evidence_id: 'ev-return-wave', category: 'weather', value: 2.8, unit: 'm', source: 'Open-Meteo Marine', timestamp: '2026-08-30T04:30:00Z', lat: 12.80, lon: 74.70, confidence: 0.95, agent: 'weather' },
          { evidence_id: 'ev-return-wind', category: 'weather', value: 38.0, unit: 'km/h', source: 'Open-Meteo Marine', timestamp: '2026-08-30T04:30:00Z', lat: 12.80, lon: 74.70, confidence: 0.95, agent: 'weather' }
        ],
        advisory: {
          advisory_category: 'SEVERE_HAZARD_OVERLAP',
          recommendation_text: 'DANGER: Your outbound journey and fishing phase look safe, but a severe wave surge (2.8m) hits your return route at 4:00 PM. This far exceeds your boat limit (1.125m). DO NOT return after 2:00 PM; return early by 1:00 PM or stay in harbor.',
          reason: 'Wave height forecast (2.8m) exceeds SVAS capsize threshold (1.125m) during return transit at 16:00 IST',
          affected_phase: 'RETURN',
          affected_time: '2026-08-30T16:00:00+05:30',
          affected_location: 'Near Mangalore Outer Channel (12.80°N, 74.70°E)',
          vessel_context: 'Vessel beam 4.5m → Max safe wave = 1.125m (SVAS BSI formula = beam/4.0). Forecast wave: 2.8m (248% of limit).',
          evidence_summary: 'Open-Meteo Marine API forecast (Tier 1 live data, HIGH confidence).',
          uncertainty_notes: 'PFZ location retrieved from INCOIS reference data.',
          disclaimer: 'SAGAR provides decision support only. Follow official alerts from INCOIS and IMD. Final command rests with the skipper.',
          language: 'en'
        },
        vessel_profile: {
          vessel_id: 'vessel-trawler-45',
          vessel_type: 'Mechanized Trawler',
          beam_width_m: 4.5,
          length_m: 14.5,
          cruising_speed_kmh: 15.0,
          safety_thresholds: {
            max_safe_wave_m: 1.125,
            rule_applied: 'SVAS_CAPSIZE_BSI',
            formula: 'beam_width_m / 4.0'
          }
        },
        weather_forecasts: [
          { waypoint_index: 0, lat: 12.87, lon: 74.84, time_iso: '2026-08-30T05:00:00+05:30', wave_height_m: 0.7, wind_speed_kmh: 12, wind_direction_deg: 210, swell_height_m: 0.4, visibility_km: 12 },
          { waypoint_index: 1, lat: 12.80, lon: 74.70, time_iso: '2026-08-30T07:00:00+05:30', wave_height_m: 0.8, wind_speed_kmh: 14, wind_direction_deg: 215, swell_height_m: 0.5, visibility_km: 10 },
          { waypoint_index: 2, lat: 12.75, lon: 74.50, time_iso: '2026-08-30T10:00:00+05:30', wave_height_m: 0.9, wind_speed_kmh: 15, wind_direction_deg: 220, swell_height_m: 0.6, visibility_km: 10 },
          { waypoint_index: 3, lat: 12.80, lon: 74.70, time_iso: '2026-08-30T16:00:00+05:30', wave_height_m: 2.8, wind_speed_kmh: 38, wind_direction_deg: 240, swell_height_m: 1.8, visibility_km: 4 },
          { waypoint_index: 4, lat: 12.87, lon: 74.84, time_iso: '2026-08-30T18:00:00+05:30', wave_height_m: 2.5, wind_speed_kmh: 32, wind_direction_deg: 235, swell_height_m: 1.5, visibility_km: 6 }
        ],
        errors: []
      },
      meta: { request_id: 'req-flagship-003', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_3_SEVERE_RETURN' }
    }
  },

  'SCENARIO_4_MISSING_INFO': {
    id: 'SCENARIO_4_MISSING_INFO',
    name: '4. Missing Information',
    badge: '⚪ INSUFFICIENT INFO',
    description: 'Vessel beam width & departure time missing -> System requests missing info without guessing safety parameters.',
    mockResponse: {
      status: 'insufficient_information',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        session_id: 'sess-missing-004',
        workflow_status: 'INSUFFICIENT_INFORMATION',
        advisory_category: 'INSUFFICIENT_INFORMATION',
        overall_risk_level: 'UNKNOWN',
        missing_data: [
          { data_type: 'vessel_beam_width', reason: 'Vessel beam width is required to calculate SVAS capsize wave threshold (beam / 4.0)', is_safety_critical: true },
          { data_type: 'departure_time', reason: 'Departure time is required for 4D temporal weather forecast alignment', is_safety_critical: true }
        ],
        recommendation_text: 'SAGAR cannot calculate a safety advisory because your boat\'s beam width and departure time are missing. We never guess safety-critical parameters.',
        disclaimer: 'SAGAR provides decision support only. Never venture out without verifying safety limits.'
      },
      meta: { request_id: 'req-missing-004', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_4_MISSING_INFO' }
    }
  },

  'SCENARIO_5_CONFLICTING': {
    id: 'SCENARIO_5_CONFLICTING',
    name: '5. Conflicting Information',
    badge: '⚠️ DATA CONFLICT',
    description: 'Official satellite forecast says high waves (2.9m), local harbor observation says calm (0.9m). Shown side-by-side.',
    mockResponse: {
      status: 'success',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        trip_id: 'trip-scenario-5',
        session_id: 'sess-conflict-005',
        workflow_status: 'COMPLETED',
        persistence_status: 'success',
        translation_provider: 'bhashini',
        language: 'en',
        overall_risk_level: 'MODERATE',
        trip_context: {
          origin: 'Karwar Harbor',
          origin_coordinates: { lat: 14.80, lon: 74.12 },
          destination_type: 'NEAREST_PFZ',
          destination_coordinates: { lat: 14.65, lon: 73.90 },
          departure_time_iso: '2026-08-30T06:00:00+05:30',
          fishing_duration_hours: 4.0,
          expected_return_time_iso: '2026-08-30T15:00:00+05:30'
        },
        trajectory: {
          route_id: 'ROUTE-CONF-05',
          total_distance_km: 78.0,
          waypoints: [
            { phase: 'OUTBOUND', lat: 14.80, lon: 74.12, eta_iso: '2026-08-30T06:00:00+05:30', name: 'Karwar Departure' },
            { phase: 'FISHING', lat: 14.65, lon: 73.90, eta_iso: '2026-08-30T09:00:00+05:30', name: 'Karwar PFZ' },
            { phase: 'RETURN', lat: 14.80, lon: 74.12, eta_iso: '2026-08-30T15:00:00+05:30', name: 'Karwar Arrival' }
          ]
        },
        alerts: [
          { alert_type: 'HIGH_WAVE', severity: 'WARNING', message: 'Discrepancy detected: Offshore forecast indicates 2.9m waves while port observation shows 0.9m.', threshold: 1.0, actual_value: 2.9 }
        ],
        visualization_spec: {
          map_center: { lat: 14.72, lon: 74.01 },
          zoom: 10,
          layers: [
            {
              layer_id: 'trajectory',
              type: 'line',
              geojson: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: [
                    [74.12, 14.80],
                    [73.90, 14.65],
                    [74.12, 14.80]
                  ]
                }
              },
              style: { color: '#f59e0b', weight: 4 }
            }
          ]
        },
        risk_evidence: {
          advisory_category: 'ELEVATED_RISK_IDENTIFIED',
          overall_risk_level: 'MODERATE',
          summary: 'Conflicting wave measurements between satellite NWP models and harbor observations.',
          is_trip_recommended: false,
          hazard_flags: [],
          data_conflicts: [
            {
              variable: 'Wave Height (Significant Wave Height)',
              source_a: { name: 'Open-Meteo Offshore Forecast', value: '2.9 m', timestamp: '2026-08-30T04:00:00Z' },
              source_b: { name: 'Local Harbor Master Coastal Observation', value: '0.9 m', timestamp: '2026-08-30T04:30:00Z' },
              conflict_indicator: 'DISCREPANCY DETECTED (+2.0m difference between offshore model & coastal observation)'
            }
          ],
          provenance_summary: [
            { source: 'Open-Meteo Marine API', fallback_tier: 1, confidence: 'HIGH' },
            { source: 'Karwar Port Office Manual Observation', fallback_tier: 2, confidence: 'MODERATE' }
          ]
        },
        evidence_registry: [
          { evidence_id: 'ev-conf-model', category: 'weather', value: 2.9, unit: 'm', source: 'Open-Meteo Model', timestamp: '2026-08-30T04:00:00Z', confidence: 0.85, agent: 'weather' },
          { evidence_id: 'ev-conf-local', category: 'weather', value: 0.9, unit: 'm', source: 'Port Master Visual Log', timestamp: '2026-08-30T04:30:00Z', confidence: 0.80, agent: 'coastal' }
        ],
        advisory: {
          advisory_category: 'ELEVATED_RISK_IDENTIFIED',
          recommendation_text: 'ATTENTION: Data sources disagree on wave height. Official Open-Meteo forecast indicates dangerous offshore waves (2.9m), while local coastal reports calm conditions (0.9m). Exercise extreme caution.',
          reason: 'Conflict between offshore satellite model forecast and local harbor report',
          vessel_context: 'Trawler (beam 4.0m) → Limit 1.0m. Local observation is safe, official forecast is unsafe.',
          disclaimer: 'SAGAR presents all sources transparently without fabricating an ungrounded consensus. Always defer to official marine advisories.',
          language: 'en'
        },
        errors: []
      },
      meta: { request_id: 'req-conflict-005', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_5_CONFLICTING' }
    }
  },

  'SCENARIO_6_GEOFENCE': {
    id: 'SCENARIO_6_GEOFENCE',
    name: '6. Geofence Restriction (MPA)',
    badge: '🛑 RESTRICTED ZONE',
    description: 'Planned route intersects Marine Protected Area (Gulf of Mannar MPA). Restricted zone overlay.',
    mockResponse: {
      status: 'success',
      data: {
        MOCK_WARNING: 'THIS IS MOCK DATA — NOT REAL',
        trip_id: 'trip-scenario-6',
        session_id: 'sess-geofence-006',
        workflow_status: 'COMPLETED',
        persistence_status: 'success',
        translation_provider: 'bhashini',
        language: 'en',
        overall_risk_level: 'HIGH',
        trip_context: {
          origin: 'Rameswaram Port',
          origin_coordinates: { lat: 9.28, lon: 79.31 },
          destination_type: 'COORDINATES',
          destination_coordinates: { lat: 9.15, lon: 79.10 },
          departure_time_iso: '2026-08-30T05:00:00+05:30',
          fishing_duration_hours: 4.0,
          expected_return_time_iso: '2026-08-30T15:00:00+05:30'
        },
        trajectory: {
          route_id: 'ROUTE-GEO-06',
          total_distance_km: 65.0,
          waypoints: [
            { phase: 'OUTBOUND', lat: 9.28, lon: 79.31, eta_iso: '2026-08-30T05:00:00+05:30', name: 'Rameswaram Departure' },
            { phase: 'FISHING', lat: 9.18, lon: 79.18, eta_iso: '2026-08-30T07:30:00+05:30', name: 'Gulf of Mannar Boundary' },
            { phase: 'FISHING', lat: 9.15, lon: 79.10, eta_iso: '2026-08-30T10:00:00+05:30', name: 'Restricted Waters' },
            { phase: 'RETURN', lat: 9.28, lon: 79.31, eta_iso: '2026-08-30T15:00:00+05:30', name: 'Rameswaram Return' }
          ],
          geofence_intersections: [
            {
              constraint_id: 'MPA-GULF-MANNAR-01',
              constraint_name: 'Gulf of Mannar Marine National Park Zone A',
              constraint_type: 'MPA',
              intersects: true,
              affected_waypoints: [1, 2],
              source: 'World Database on Protected Areas (WDPA)'
            }
          ]
        },
        alerts: [
          { alert_type: 'GEOFENCE_VIOLATION', severity: 'SEVERE', message: 'Planned trajectory intersects strictly prohibited Marine National Park no-take sanctuary.', threshold: 0, actual_value: 1 }
        ],
        visualization_spec: {
          map_center: { lat: 9.21, lon: 79.20 },
          zoom: 11,
          layers: [
            {
              layer_id: 'trajectory',
              type: 'line',
              geojson: {
                type: 'Feature',
                properties: {},
                geometry: {
                  type: 'LineString',
                  coordinates: [
                    [79.31, 9.28],
                    [79.18, 9.18],
                    [79.10, 9.15],
                    [79.31, 9.28]
                  ]
                }
              },
              style: { color: '#ef4444', weight: 4 }
            },
            {
              layer_id: 'restricted_zones',
              type: 'polygon',
              geojson: {
                type: 'Feature',
                properties: { name: 'Gulf of Mannar Marine National Park' },
                geometry: {
                  type: 'Polygon',
                  coordinates: [[
                    [79.05, 9.10],
                    [79.25, 9.10],
                    [79.25, 9.22],
                    [79.05, 9.22],
                    [79.05, 9.10]
                  ]]
                }
              },
              style: { color: '#dc2626', fillOpacity: 0.25 }
            }
          ]
        },
        risk_evidence: {
          advisory_category: 'CONSIDER_ROUTE_TIME_MODIFICATION',
          overall_risk_level: 'HIGH',
          is_trip_recommended: false,
          rule_results: [
            {
              rule_id: 'RULE_GEOFENCE_MPA_01',
              rule_name: 'Marine Protected Area Compliance',
              status: 'FAILED',
              risk_level: 'HIGH',
              details: 'Waypoints 1 and 2 violate Gulf of Mannar Marine National Park No-Take Boundary.',
              evidence: { mpa_id: 'MPA-GULF-MANNAR-01', violations_count: 2 }
            }
          ],
          hazard_flags: [
            {
              trip_phase: 'FISHING',
              hazard_type: 'GEOFENCE_VIOLATION',
              waypoint_index: 2,
              location: { lat: 9.15, lon: 79.10 },
              time_iso: '2026-08-30T10:00:00+05:30',
              observed_value: 1,
              threshold_value: 0,
              rule_applied: 'MPA_NO_TAKE_BOUNDARY_CHECK',
              provenance: { source: 'WDPA / Fisheries Dept GIS Layer', retrieved_at: new Date().toISOString(), fallback_tier: 1, confidence: 'HIGH' }
            }
          ],
          geofence_violations: [
            { zone: 'Gulf of Mannar Marine Protected Area', type: 'NO_TAKE_ZONE', action_required: 'Reroute outside boundary polygon' }
          ],
          provenance_summary: [
            { source: 'WDPA Sanctuary Polygon GIS Layer', fallback_tier: 1, confidence: 'HIGH' }
          ]
        },
        evidence_registry: [
          { evidence_id: 'ev-geo-01', category: 'gis', value: 'INTERSECTING_ZONE_A', unit: 'status', source: 'WDPA Sanctuary DB', timestamp: '2026-08-30T00:00:00Z', confidence: 1.0, agent: 'geo' }
        ],
        advisory: {
          advisory_category: 'CONSIDER_ROUTE_TIME_MODIFICATION',
          recommendation_text: 'ROUTE ALERT: Your planned route crosses the Gulf of Mannar Marine National Park boundary where fishing is strictly prohibited. Please modify your destination coordinates to stay outside the reserve.',
          reason: 'Trajectory intersects Marine Protected Area (MPA-GULF-MANNAR-01)',
          affected_phase: 'FISHING',
          affected_location: 'Gulf of Mannar Protected Zone (9.15°N, 79.10°E)',
          disclaimer: 'SAGAR displays verified GIS spatial boundary checks.',
          language: 'en'
        },
        errors: []
      },
      meta: { request_id: 'req-geo-006', timestamp: new Date().toISOString(), version: 'v1', scenario_id: 'SCENARIO_6_GEOFENCE' }
    }
  }
};
