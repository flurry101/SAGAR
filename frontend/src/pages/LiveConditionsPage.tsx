import React, { useCallback, useEffect, useState } from 'react';
import { AlertTriangle, CloudSun, Fish, Gauge, MapPin, Mountain, RefreshCw, Waves } from 'lucide-react';
import { AdapterProvenance, directAdapterApi, DirectAdapterResponse } from '../api/directAdapterApi';

type Results = {
  weather?: DirectAdapterResponse;
  hazards?: DirectAdapterResponse;
  pfz?: DirectAdapterResponse;
  marine?: DirectAdapterResponse;
  tides?: DirectAdapterResponse;
  bathymetry?: DirectAdapterResponse;
};

const tierClass = (tier?: number) => tier === 1
  ? 'bg-emerald-50 border-emerald-300 text-emerald-800'
  : 'bg-amber-50 border-amber-300 text-amber-800';

const ProvenanceBadge: React.FC<{ provenance?: AdapterProvenance }> = ({ provenance }) => {
  const tier = provenance?.fallback_tier ?? 3;
  return (
    <div className={`rounded-lg border px-2.5 py-2 text-[11px] font-semibold ${tierClass(tier)}`}>
      <div>Tier {tier} {tier === 1 ? 'live data' : 'fallback data'}</div>
      <div className="mt-0.5 font-normal leading-snug">Source: {provenance?.source || 'not supplied by adapter'}</div>
    </div>
  );
};

const Value: React.FC<{ label: string; value: React.ReactNode }> = ({ label, value }) => (
  <div className="flex justify-between gap-3 border-b border-sagar-borderLight py-2 last:border-0">
    <span className="text-slate-500">{label}</span>
    <strong className="text-right font-mono text-sagar-navy">{value ?? 'Unavailable'}</strong>
  </div>
);

export const LiveConditionsPage: React.FC = () => {
  const [lat, setLat] = useState('12.87');
  const [lon, setLon] = useState('74.84');
  const [results, setResults] = useState<Results>({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async () => {
    const latitude = Number(lat);
    const longitude = Number(lon);
    if (!Number.isFinite(latitude) || !Number.isFinite(longitude) || latitude < -90 || latitude > 90 || longitude < -180 || longitude > 180) {
      setError('Enter a valid latitude and longitude.');
      return;
    }

    setLoading(true);
    setError(null);
    const coordinate = { lat: latitude, lon: longitude };
    const etaIso = new Date().toISOString().replace(/\.\d{3}Z$/, 'Z');
    const [weather, hazards, pfz, marine, tides, bathymetry] = await Promise.all([
      directAdapterApi.weatherForecast(coordinate, etaIso),
      directAdapterApi.weatherHazards(coordinate),
      directAdapterApi.potentialFishingZones(coordinate),
      directAdapterApi.marineObservations(coordinate, etaIso),
      directAdapterApi.tides(coordinate, etaIso),
      directAdapterApi.bathymetry(coordinate),
    ]);
    setResults({ weather, hazards, pfz, marine, tides, bathymetry });
    const failed = [weather, hazards, pfz, marine, tides, bathymetry].filter((response) => response.status === 'error');
    if (failed.length) setError(`${failed.length} adapter request${failed.length === 1 ? '' : 's'} failed. The remaining results are shown.`);
    setLoading(false);
  }, [lat, lon]);

  useEffect(() => { void load(); }, [load]);

  const weather = results.weather?.data?.observations?.[0]?.weather;
  const hazardData = results.hazards?.data;
  const hazards = hazardData?.hazards || [];
  const pfzData = results.pfz?.data;
  const marine = results.marine?.data?.observations?.[0]?.marine;
  const tide = results.tides?.data?.tides?.[0];
  const depth = results.bathymetry?.data?.bathymetry?.[0];

  return (
    <main className="mx-auto max-w-6xl px-4 py-8 sm:px-6">
      <div className="mb-6 rounded-2xl border border-sky-200 bg-sky-50/90 p-5">
        <div className="flex items-start gap-3">
          <Waves className="mt-0.5 h-6 w-6 text-sky-700" />
          <div>
            <h1 className="text-xl font-black text-sagar-navy">Direct marine conditions</h1>
            <p className="mt-1 text-sm text-slate-600">Calls six M4 adapter endpoints directly. No trip assessment, chat, graph, or LLM is involved.</p>
          </div>
        </div>
        <div className="mt-4 flex flex-wrap items-end gap-3">
          <label className="text-xs font-bold text-slate-600">Latitude<input aria-label="Latitude" value={lat} onChange={(event) => setLat(event.target.value)} className="mt-1 block w-32 rounded-lg border border-sagar-border bg-white px-3 py-2 font-mono text-sm" /></label>
          <label className="text-xs font-bold text-slate-600">Longitude<input aria-label="Longitude" value={lon} onChange={(event) => setLon(event.target.value)} className="mt-1 block w-32 rounded-lg border border-sagar-border bg-white px-3 py-2 font-mono text-sm" /></label>
          <button onClick={() => void load()} disabled={loading} className="inline-flex items-center gap-2 rounded-lg bg-sky-700 px-4 py-2 text-sm font-bold text-white disabled:opacity-60"><RefreshCw className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`} />{loading ? 'Loading…' : 'Load conditions'}</button>
        </div>
        {error && <p className="mt-3 text-sm font-semibold text-rose-700">{error}</p>}
      </div>

      <div className="grid gap-4 md:grid-cols-2">
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><CloudSun className="h-5 w-5 text-sky-600" /><h2 className="font-bold text-sagar-navy">Weather and sea state</h2></div><Value label="Wave height" value={weather?.wave_height_m != null ? `${weather.wave_height_m} m` : null} /><Value label="Wind speed" value={weather?.wind_speed_kmh != null ? `${weather.wind_speed_kmh} km/h` : null} /><Value label="Swell height" value={weather?.swell_height_m != null ? `${weather.swell_height_m} m` : null} /><div className="mt-4"><ProvenanceBadge provenance={weather?.provenance} /></div></section>
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><AlertTriangle className="h-5 w-5 text-amber-600" /><h2 className="font-bold text-sagar-navy">Hazards</h2></div><Value label="Active hazards" value={hazards.length} /><Value label="Cyclone active" value={hazardData?.cyclone_active ? 'Yes' : 'No'} />{hazards[0] && <p className="mt-3 text-sm text-slate-600">{hazards[0].description}</p>}<div className="mt-4"><ProvenanceBadge provenance={hazardData?.provenance || hazards[0]?.provenance} /></div></section>
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><Fish className="h-5 w-5 text-teal-600" /><h2 className="font-bold text-sagar-navy">Potential fishing zones</h2></div><Value label="PFZ zones returned" value={pfzData?.pfzs?.length ?? 0} />{pfzData?.pfzs?.[0] && <Value label="Nearest zone" value={`${pfzData.pfzs[0].coordinates.lat}, ${pfzData.pfzs[0].coordinates.lon}`} />}<div className="mt-4"><ProvenanceBadge provenance={pfzData?.provenance || pfzData?.pfzs?.[0]?.provenance} /></div></section>
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><MapPin className="h-5 w-5 text-indigo-600" /><h2 className="font-bold text-sagar-navy">Ocean observations</h2></div><Value label="Sea-surface temperature" value={marine?.sst_celsius != null ? `${marine.sst_celsius} °C` : null} /><Value label="Chlorophyll" value={marine?.chlorophyll_mg_m3 != null ? `${marine.chlorophyll_mg_m3} mg/m³` : null} /><Value label="HAB detected" value={marine?.hab_detected == null ? null : marine.hab_detected ? 'Yes' : 'No'} /><div className="mt-4"><ProvenanceBadge provenance={marine?.provenance} /></div></section>
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><Gauge className="h-5 w-5 text-cyan-600" /><h2 className="font-bold text-sagar-navy">Tides</h2></div><Value label="Current tide height" value={tide?.tide_height_m != null ? `${tide.tide_height_m} m` : null} /><Value label="Next high tide" value={tide?.next_high_time_iso ? new Date(tide.next_high_time_iso).toLocaleString() : null} /><Value label="Next low tide" value={tide?.next_low_time_iso ? new Date(tide.next_low_time_iso).toLocaleString() : null} /><div className="mt-4"><ProvenanceBadge provenance={tide?.provenance} /></div></section>
        <section className="rounded-2xl border border-sagar-border bg-white p-5 shadow-soft-sm"><div className="mb-4 flex items-center gap-2"><Mountain className="h-5 w-5 text-slate-600" /><h2 className="font-bold text-sagar-navy">Seabed depth</h2></div><Value label="Depth / elevation" value={depth?.depth_m != null ? `${depth.depth_m} m` : null} /><Value label="Surface type" value={depth?.surface_type} /><Value label="Checked position" value={depth ? `${Number(depth.lat).toFixed(3)}°, ${Number(depth.lon).toFixed(3)}°` : null} /><div className="mt-4"><ProvenanceBadge provenance={depth?.provenance} /></div></section>
      </div>
    </main>
  );
};
