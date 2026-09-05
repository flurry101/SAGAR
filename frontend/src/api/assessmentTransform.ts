import { APIResponse, AssessmentData } from '../types/api';
import { ProvenanceSummary } from '../types/provenance';

type AnyRecord = Record<string, any>;

const asProvenance = (value: AnyRecord | undefined, fallbackSource: string) => ({
  source: value?.source || fallbackSource,
  retrieved_at: value?.retrieved_at,
  validity_time: value?.validity_time,
  fallback_tier: value?.fallback_tier ?? 3,
  confidence: value?.confidence || 'LOW',
});

/**
 * Adapt the graph's Step-09 envelope to the view model used by AdvisoryPage.
 * The graph deliberately keeps adapter data nested by waypoint; the UI cards
 * consume a flat presentation model.  Keep this translation at the boundary
 * so the backend response remains its documented graph contract.
 */
export function normalizeAssessmentResponse(response: APIResponse): APIResponse {
  if (!response.data || response.status === 'error') return response;

  const data = response.data as AssessmentData & AnyRecord;
  const weatherForecasts = (data.weather_observations || []).map((item: AnyRecord) => {
    const weather = item.weather || item;
    return {
      ...weather,
      waypoint_index: item.waypoint_index,
      phase: item.phase,
      lat: item.lat ?? weather.lat,
      lon: item.lon ?? weather.lon,
      time_iso: item.time_iso ?? weather.time_iso,
      stale: weather.resolved === false || weather.provenance?.fallback_tier !== 1,
      provenance: asProvenance(weather.provenance, 'Open-Meteo (unresolved)'),
    };
  });

  const marineObservations = (data.marine_observations || []).map((item: AnyRecord) => {
    const marine = item.marine || item;
    return {
      ...marine,
      waypoint_index: item.waypoint_index,
      phase: item.phase,
      lat: item.lat ?? marine.lat,
      lon: item.lon ?? marine.lon,
      time_iso: item.time_iso ?? marine.time_iso,
      chlorophyll_mgm3: marine.chlorophyll_mgm3 ?? marine.chlorophyll_mg_m3,
      provenance: asProvenance(marine.provenance, 'Marine observation unavailable'),
    };
  });

  const pfzData = data.pfz_data || {};
  let rawPfzZones = [];
  if (Array.isArray(data.pfz_data)) {
    rawPfzZones = data.pfz_data;
  } else if (Array.isArray(pfzData.pfzs)) {
    rawPfzZones = pfzData.pfzs;
  } else if (Array.isArray(data.pfz_zones)) {
    rawPfzZones = data.pfz_zones;
  }
  
  const pfzZones = rawPfzZones.map((pfz: AnyRecord, index: number) => {
  const geometry = pfz.geometry;

  // Live INCOIS PFZ can arrive as a GeoJSON LineString:
  // coordinates = [[lon, lat], [lon, lat], ...]
  const firstCoordinate =
    geometry?.type === 'LineString' &&
    Array.isArray(geometry.coordinates) &&
    Array.isArray(geometry.coordinates[0])
      ? geometry.coordinates[0]
      : undefined;

  return {
    pfz_id: pfz.pfz_id || `PFZ-${index + 1}`,

    coordinates: {
      lat:
        pfz.coordinates?.lat ??
        pfz.lat ??
        firstCoordinate?.[1],

      lon:
        pfz.coordinates?.lon ??
        pfz.lon ??
        firstCoordinate?.[0],
    },

    valid_from: pfz.valid_from ?? pfz.validity_start,
    valid_until: pfz.valid_until ?? pfz.validity_end,

    distance_from_origin_km:
      pfz.distance_km ??
      pfz.distance_from_origin_km ??
      0,

    available: pfz.available ?? true,

    // IMPORTANT: preserve the full INCOIS geometry
    geometry,

    provenance: asProvenance(
      pfz.provenance || pfzData.provenance,
      'PFZ unavailable'
    ),
  };
  });

  const sources = [
  ...weatherForecasts.map((item: AnyRecord) => item.provenance),
  ...marineObservations.map((item: AnyRecord) => item.provenance),
  ...pfzZones.map((item: AnyRecord) => item.provenance),

  // The current graph emits GDACS/static-hazard alerts without provenance.
  // Its adapter is explicitly Tier 3, so make that limitation visible.
  ...(data.alerts || []).map(
    (alert: AnyRecord) =>
      asProvenance(
        alert.provenance,
        `${alert.source || 'Hazard source'} (Tier unavailable in graph payload)`
      )
  ),
];

  const provenanceSummary: ProvenanceSummary[] = Array.from(
    new Map(sources.map((source: AnyRecord) => [`${source.source}:${source.fallback_tier}`, source])).values(),
  ).map((source: AnyRecord) => ({
    source: String(source.source),
    retrieved_at: source.retrieved_at,
    validity_time: source.validity_time,
    fallback_tier: source.fallback_tier as 1 | 2 | 3,
    confidence: source.confidence as 'HIGH' | 'MODERATE' | 'LOW',
  }));

  return {
    ...response,
    data: {
      ...data,
      weather_forecasts: weatherForecasts,
      marine_observations: marineObservations,
      pfz_zones: pfzZones,
      pfz_available: pfzZones.length > 0,
      risk_evidence: data.risk_evidence
        ? { ...data.risk_evidence, provenance_summary: provenanceSummary }
        : data.risk_evidence,
    },
  };
}
