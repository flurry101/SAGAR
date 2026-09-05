const fs = require('fs');

function asProvenance(value, fallbackSource) {
  return {
    source: value?.source || fallbackSource,
    retrieved_at: value?.retrieved_at,
    validity_time: value?.validity_time,
    fallback_tier: value?.fallback_tier ?? 3,
    confidence: value?.confidence || 'LOW',
  };
}

function normalizeAssessmentResponse(response) {
  if (!response.data || response.status === 'error') return response;

  const data = response.data;
  const weatherForecasts = (data.weather_observations || []).map((item) => {
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

  const marineObservations = (data.marine_observations || []).map((item) => {
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
  const rawPfzZones = pfzData.pfzs || data.pfz_zones || [];
  const pfzZones = rawPfzZones.map((pfz, index) => {
    const geometry = pfz.geometry;

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

      geometry,

      provenance: asProvenance(
        pfz.provenance || pfzData.provenance,
        'PFZ unavailable'
      ),
    };
  });

  const sources = [
    ...weatherForecasts.map((item) => item.provenance),
    ...marineObservations.map((item) => item.provenance),
    ...pfzZones.map((item) => item.provenance),
    ...(data.alerts || []).map(
      (alert) =>
        asProvenance(
          alert.provenance,
          `${alert.source || 'Hazard source'} (Tier unavailable in graph payload)`
        )
    ),
  ];

  const provenanceSummary = Array.from(
    new Map(sources.map((source) => [`${source.source}:${source.fallback_tier}`, source])).values(),
  ).map((source) => ({
    source: String(source.source),
    retrieved_at: source.retrieved_at,
    validity_time: source.validity_time,
    fallback_tier: source.fallback_tier,
    confidence: source.confidence,
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

try {
  const data = JSON.parse(fs.readFileSync('response.json', 'utf8'));
  const response = { status: 'success', data: data };
  const normalized = normalizeAssessmentResponse(response);
  console.log("Normalization successful!");
} catch (e) {
  console.error("Error during normalization:", e);
}
