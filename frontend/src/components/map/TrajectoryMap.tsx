import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer, ScatterplotLayer, PathLayer, TextLayer } from '@deck.gl/layers';
import { Trajectory, Waypoint } from '../../types/trip';
import { HazardFlag } from '../../types/risk';
import { PFZZone, VisualizationSpec, RouteCandidate } from '../../types/api';
import { useAppStore } from '../../state/appStore';
import { Navigation, Maximize2, ShieldAlert, Sparkles, MapPin, Anchor, Waves, Info } from 'lucide-react';
import { useReducedMotion } from 'framer-motion';
import { Trans, useLingui } from '@lingui/react/macro';

interface Props {
  trajectory?: Trajectory;
  hazardFlags?: HazardFlag[];
  pfzZones?: PFZZone[];
  visualizationSpec?: VisualizationSpec;
  routeCandidates?: RouteCandidate[];
}

interface TooltipInfo {
  x: number;
  y: number;
  title: string;
  subtitle?: string;
  phase?: string;
  eta?: string;
  coords?: string;
  riskBadge?: { text: string; bg: string; border: string; color: string };
  hazardDetail?: string;
  pfzDetail?: { sst: string; chlorophyll: string; confidence: string };
}

export const TrajectoryMap: React.FC<Props> = ({
  trajectory,
  hazardFlags = [],
  pfzZones = [],
  visualizationSpec,
  routeCandidates = [],
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckOverlayRef = useRef<MapboxOverlay | null>(null);
  const animFrameRef = useRef<number | null>(null);
  const vesselAnimRef = useRef<number | null>(null);

  const { t } = useLingui();
  const shouldReduceMotion = useReducedMotion();
  const { selectedWaypointIndex, setSelectedWaypointIndex, selectedRouteCandidateId } = useAppStore();

  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);
  const [vesselProgress, setVesselProgress] = useState<number>(0);
  const [pulsePhase, setPulsePhase] = useState<number>(0);

  const activeCandidate = routeCandidates.find((r) => r.route_id === selectedRouteCandidateId);
  const activeWaypoints: Waypoint[] = useMemo(() => {
    return activeCandidate?.waypoints || trajectory?.waypoints || [];
  }, [activeCandidate, trajectory]);

  // Determine if active route has a severe return hazard
  const hasSevereHazard = useMemo(() => {
    return hazardFlags.some(
      (h) => h.trip_phase === 'RETURN' || h.observed_value >= h.threshold_value * 1.25
    );
  }, [hazardFlags]);

  // Primary route color [R, G, B, A]
  const primaryRouteColor: [number, number, number, number] = useMemo(() => {
    if ((activeCandidate && activeCandidate.score < 50) || hasSevereHazard) {
      return [220, 38, 38, 240]; // Severe Risk Red
    }
    return [2, 132, 199, 240]; // SAGAR Ocean Blue
  }, [activeCandidate, hasSevereHazard]);

  // 1. Initialize MapLibre GL Map & Deck.gl MapboxOverlay
  useEffect(() => {
    if (!mapContainer.current || mapRef.current) return;

    const initialCenter: [number, number] = visualizationSpec?.map_center
      ? [visualizationSpec.map_center.lon, visualizationSpec.map_center.lat]
      : activeWaypoints[0]
      ? [activeWaypoints[0].lon, activeWaypoints[0].lat]
      : [74.84, 12.87]; // Mangalore Harbor default

    const map = new maplibregl.Map({
      container: mapContainer.current,
      style: {
        version: 8,
        sources: {
          'osm-tiles': {
            type: 'raster',
            tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
            tileSize: 256,
            attribution: '© OpenStreetMap contributors',
          },
        },
        layers: [
          {
            id: 'osm-layer',
            type: 'raster',
            source: 'osm-tiles',
            minzoom: 0,
            maxzoom: 19,
          },
        ],
      },
      center: initialCenter,
      zoom: visualizationSpec?.zoom || 9,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), 'top-right');

    // Create Deck.gl MapboxOverlay instance and attach as a MapLibre control
    const deckOverlay = new MapboxOverlay({
      interleaved: true,
      layers: [],
    });
    map.addControl(deckOverlay as any);
    deckOverlayRef.current = deckOverlay;
    mapRef.current = map;

    return () => {
      if (animFrameRef.current) cancelAnimationFrame(animFrameRef.current);
      if (vesselAnimRef.current) cancelAnimationFrame(vesselAnimRef.current);
      if (deckOverlayRef.current) {
        map.removeControl(deckOverlayRef.current as any);
        deckOverlayRef.current = null;
      }
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 2. Continuous Vessel & Pulse Animation Loop (60fps smooth WebGL loop)
  useEffect(() => {
    if (shouldReduceMotion) return;

    let startTime = performance.now();
    const duration = 14000; // 14 seconds per round-trip voyage loop

    const animateLoop = (time: number) => {
      const elapsed = (time - startTime) % duration;
      const progress = elapsed / duration;
      setVesselProgress(progress);
      setPulsePhase((prev) => (prev + 0.05) % (Math.PI * 2));
      vesselAnimRef.current = requestAnimationFrame(animateLoop);
    };

    vesselAnimRef.current = requestAnimationFrame(animateLoop);
    return () => {
      if (vesselAnimRef.current) cancelAnimationFrame(vesselAnimRef.current);
    };
  }, [shouldReduceMotion]);

  // Compute moving vessel coordinates based on vesselProgress
  const currentVesselPosition = useMemo(() => {
    if (activeWaypoints.length === 0) return null;
    if (activeWaypoints.length === 1) return [activeWaypoints[0].lon, activeWaypoints[0].lat];

    const totalSegments = activeWaypoints.length - 1;
    const scaledProgress = vesselProgress * totalSegments;
    const segmentIndex = Math.min(Math.floor(scaledProgress), totalSegments - 1);
    const segmentFraction = scaledProgress - segmentIndex;

    const p1 = activeWaypoints[segmentIndex];
    const p2 = activeWaypoints[segmentIndex + 1];

    const lon = p1.lon + (p2.lon - p1.lon) * segmentFraction;
    const lat = p1.lat + (p2.lat - p1.lat) * segmentFraction;

    return [lon, lat];
  }, [activeWaypoints, vesselProgress]);

  // 3. Build Deck.gl Layers
  const buildDeckLayers = useCallback(() => {
    const layers: any[] = [];

    // A. Spec Layers (Backend GeoJSON Hazard/Restricted Polygons & Lines)
    if (visualizationSpec?.layers && visualizationSpec.layers.length > 0) {
      visualizationSpec.layers.forEach((specLayer, idx) => {
        if (specLayer.geojson) {
          layers.push(
            new GeoJsonLayer({
              id: `spec-geojson-${specLayer.layer_id || idx}`,
              data: specLayer.geojson,
              pickable: true,
              filled: true,
              stroked: true,
              lineWidthUnits: 'pixels',
              getLineWidth: specLayer.style?.weight || 3,
              getFillColor: () => {
                if (specLayer.type === 'polygon') {
                  const hex = specLayer.style?.color || '#ef4444';
                  if (hex.includes('red') || hex.includes('dc2626') || hex.includes('ef4444')) {
                    return [220, 38, 38, 45];
                  }
                  if (hex.includes('amber') || hex.includes('f59e0b')) {
                    return [217, 119, 6, 45];
                  }
                  return [147, 51, 234, 40]; // geofence purple
                }
                return [2, 132, 199, 40];
              },
              getLineColor: () => {
                const hex = specLayer.style?.color || '#0284c7';
                if (hex.includes('red') || hex.includes('dc2626') || hex.includes('ef4444')) {
                  return [220, 38, 38, 200];
                }
                if (hex.includes('amber') || hex.includes('f59e0b')) {
                  return [217, 119, 6, 200];
                }
                return [2, 132, 199, 200];
              },
              onHover: (info: any) => {
                if (info.object && info.x && info.y) {
                  const props = info.object.properties || {};
                  setTooltip({
                    x: info.x,
                    y: info.y,
                    title: props.name || (specLayer as any).title || t`Marine Zone (${specLayer.layer_id})`,
                    subtitle: props.hazard_type || props.type || t`Regulated Boundary`,
                    riskBadge: {
                      text: props.severity || t`RESTRICTED / GEOFENCE`,
                      bg: '#fef2f2',
                      border: '#fecaca',
                      color: '#991b1b',
                    },
                    hazardDetail: props.description || t`Monitored via spatio-temporal boundary geofence.`,
                  });
                } else {
                  setTooltip(null);
                }
              },
            })
          );
        }
      });
    }

    // B. Alternative Route Candidates (PathLayer)
    if (routeCandidates.length > 0) {
      const altCandidates = routeCandidates.filter((r) => r.route_id !== selectedRouteCandidateId);
      const altPathsData = altCandidates.map((c) => ({
        path: c.waypoints.map((w) => [w.lon, w.lat]),
        candidate: c,
      }));

      if (altPathsData.length > 0) {
        layers.push(
          new PathLayer({
            id: 'deck-alt-routes',
            data: altPathsData,
            pickable: true,
            widthUnits: 'pixels',
            widthMinPixels: 2.5,
            getPath: (d: any) => d.path,
            getColor: [100, 116, 139, 140], // Muted slate for non-selected routes
            getWidth: 3,
            onHover: (info: any) => {
              if (info.object && info.x && info.y) {
                const c = info.object.candidate;
                setTooltip({
                  x: info.x,
                  y: info.y,
                  title: c.name || t`Alternative Route (${c.route_id})`,
                  subtitle: t`Safety Score: ${c.score}/100`,
                  riskBadge: {
                    text: c.score >= 70 ? t`FAVOURABLE` : t`MODERATE RISK`,
                    bg: c.score >= 70 ? '#f0fdf4' : '#fffbeb',
                    border: c.score >= 70 ? '#86efac' : '#fcd34d',
                    color: c.score >= 70 ? '#166534' : '#92400e',
                  },
                });
              } else {
                setTooltip(null);
              }
            },
          })
        );
      }
    }

    // C. Primary Active Voyage Trajectory (PathLayer)
    if (activeWaypoints.length > 1) {
      const primaryPathData = [
        {
          path: activeWaypoints.map((w) => [w.lon, w.lat]),
        },
      ];

      // Outer soft glowing line
      layers.push(
        new PathLayer({
          id: 'deck-primary-glow',
          data: primaryPathData,
          pickable: false,
          widthUnits: 'pixels',
          widthMinPixels: 8,
          getPath: (d: any) => d.path,
          getColor: [primaryRouteColor[0], primaryRouteColor[1], primaryRouteColor[2], 50],
          getWidth: 9,
        })
      );

      // Core trajectory line
      layers.push(
        new PathLayer({
          id: 'deck-primary-route',
          data: primaryPathData,
          pickable: true,
          widthUnits: 'pixels',
          widthMinPixels: 4,
          getPath: (d: any) => d.path,
          getColor: primaryRouteColor,
          getWidth: 4.5,
        })
      );
    }

    // D. Potential Fishing Zones (PFZ Satellite grounds - ScatterplotLayer)
    if (pfzZones && pfzZones.length > 0) {
      const pulseRadius = 14 + Math.sin(pulsePhase) * 3;

      // Soft Pulse Outer Ring
      layers.push(
        new ScatterplotLayer({
          id: 'deck-pfz-glow',
          data: pfzZones,
          pickable: false,
          radiusUnits: 'pixels',
          getPosition: (d: PFZZone) => [d.coordinates.lon, d.coordinates.lat],
          getRadius: pulseRadius,
          getFillColor: [5, 150, 105, 50], // Soft emerald glow
          getLineWidth: 0,
        })
      );

      // Center PFZ Anchor Target
      layers.push(
        new ScatterplotLayer({
          id: 'deck-pfz-points',
          data: pfzZones,
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: PFZZone) => [d.coordinates.lon, d.coordinates.lat],
          getRadius: 8.5,
          getFillColor: [5, 150, 105, 230],
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2.5,
          lineWidthUnits: 'pixels',
          onHover: (info: any) => {
            if (info.object && info.x && info.y) {
              const pfz: PFZZone = info.object;
              setTooltip({
                x: info.x,
                y: info.y,
                title: t`Potential Fishing Zone (${pfz.pfz_id})`,
                subtitle: t`Satellite Pelagic Fish Aggregation Area`,
                coords: `${pfz.coordinates.lat.toFixed(2)}°N, ${pfz.coordinates.lon.toFixed(2)}°E`,
                riskBadge: {
                  text: pfz.available ? t`PFZ ACTIVE` : t`PFZ EXPIRED`,
                  bg: '#ecfdf5',
                  border: '#a7f3d0',
                  color: '#065f46',
                },
                pfzDetail: {
                  sst: t`${pfz.distance_from_origin_km} km Outbound`,
                  chlorophyll: t`Satellite Aggregation`,
                  confidence: t`INCOIS Verified`,
                },
              });
            } else {
              setTooltip(null);
            }
          },
        })
      );
    }

    // E. Interactive Waypoints Nodes (ScatterplotLayer)
    if (activeWaypoints.length > 0) {
      layers.push(
        new ScatterplotLayer({
          id: 'deck-waypoints-nodes',
          data: activeWaypoints.map((w, idx) => ({ ...w, waypoint_index: idx })),
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: any) => [d.lon, d.lat],
          getRadius: (d: any) => (d.waypoint_index === selectedWaypointIndex ? 10 : 7),
          getFillColor: (d: any) => {
            const hasHazard = hazardFlags.some(
              (h) => h.waypoint_index === d.waypoint_index || (h.trip_phase === 'RETURN' && d.phase === 'RETURN')
            );
            if (hasHazard) return [220, 38, 38, 240]; // Severe Red
            if (d.waypoint_index === 0) return [16, 185, 129, 240]; // Departure Green
            return [2, 132, 199, 240]; // Ocean Blue
          },
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2.5,
          lineWidthUnits: 'pixels',
          onHover: (info: any) => {
            if (info.object && info.x && info.y) {
              const wp = info.object;
              const hazard = hazardFlags.find(
                (h) => h.waypoint_index === wp.waypoint_index || (h.trip_phase === 'RETURN' && wp.phase === 'RETURN')
              );

              setTooltip({
                x: info.x,
                y: info.y,
                title: wp.name || t`Waypoint ${wp.waypoint_index + 1}`,
                phase: wp.phase,
                eta: wp.eta_iso ? new Date(wp.eta_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : undefined,
                coords: `${wp.lat.toFixed(2)}°N, ${wp.lon.toFixed(2)}°E`,
                riskBadge: hazard
                  ? {
                      text: t`SEVERE: ${hazard.hazard_type.replace(/_/g, ' ')}`,
                      bg: '#fef2f2',
                      border: '#fecaca',
                      color: '#991b1b',
                    }
                  : {
                      text: t`FAVOURABLE SEA STATE`,
                      bg: '#f0fdf4',
                      border: '#bbf7d0',
                      color: '#166534',
                    },
                hazardDetail: hazard
                  ? t`${hazard.observed_value}m wave surge exceeds your boat's SVAS limit of ${hazard.threshold_value}m`
                  : undefined,
              });
            } else {
              setTooltip(null);
            }
          },
          onClick: (info: any) => {
            if (info.object && typeof info.object.waypoint_index === 'number') {
              setSelectedWaypointIndex(info.object.waypoint_index);
            }
          },
        })
      );
    }

    // F. Animated Vessel Position Marker (ScatterplotLayer)
    if (currentVesselPosition && !shouldReduceMotion) {
      // Vessel Outer Radar Sweep Ring
      layers.push(
        new ScatterplotLayer({
          id: 'deck-vessel-ping',
          data: [{ position: currentVesselPosition }],
          pickable: false,
          radiusUnits: 'pixels',
          getPosition: (d: any) => d.position,
          getRadius: 16 + Math.sin(pulsePhase * 2) * 4,
          getFillColor: [2, 132, 199, 45],
          getLineColor: [2, 132, 199, 140],
          getLineWidth: 1.5,
          lineWidthUnits: 'pixels',
        })
      );

      // Vessel Core Indicator Dot
      layers.push(
        new ScatterplotLayer({
          id: 'deck-vessel-marker',
          data: [{ position: currentVesselPosition }],
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: any) => d.position,
          getRadius: 6,
          getFillColor: [14, 165, 233, 255],
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
          onHover: (info: any) => {
            if (info.object && info.x && info.y) {
              setTooltip({
                x: info.x,
                y: info.y,
                title: t`Simulated Boat Transit Position`,
                subtitle: t`4D Spatio-Temporal Journey Tracking`,
                riskBadge: {
                  text: t`LIVE SIMULATION`,
                  bg: '#e0f2fe',
                  border: '#bae6fd',
                  color: '#0369a1',
                },
              });
            } else {
              setTooltip(null);
            }
          },
        })
      );
    }

    return layers;
  }, [
    visualizationSpec,
    routeCandidates,
    selectedRouteCandidateId,
    activeWaypoints,
    primaryRouteColor,
    pfzZones,
    pulsePhase,
    hazardFlags,
    selectedWaypointIndex,
    currentVesselPosition,
    shouldReduceMotion,
  ]);

  // 4. Update Deck.gl Overlay when state/layers change
  useEffect(() => {
    if (!deckOverlayRef.current) return;
    const layers = buildDeckLayers();
    deckOverlayRef.current.setProps({ layers });
  }, [buildDeckLayers]);

  // 5. Center & Highlight Selected Waypoint
  useEffect(() => {
    const map = mapRef.current;
    if (!map || selectedWaypointIndex === null || !activeWaypoints[selectedWaypointIndex]) return;

    const targetWp = activeWaypoints[selectedWaypointIndex];
    map.flyTo({
      center: [targetWp.lon, targetWp.lat],
      zoom: 11.2,
      speed: 1.2,
      curve: 1.4,
    });
  }, [selectedWaypointIndex, activeWaypoints]);

  // 6. Reset Bounds
  const handleResetBounds = () => {
    const map = mapRef.current;
    if (!map || activeWaypoints.length === 0) return;
    const bounds = new maplibregl.LngLatBounds();
    activeWaypoints.forEach((wp) => bounds.extend([wp.lon, wp.lat]));
    if (pfzZones && pfzZones.length > 0) {
      pfzZones.forEach((pfz) => bounds.extend([pfz.coordinates.lon, pfz.coordinates.lat]));
    }
    map.fitBounds(bounds, { padding: 50, maxZoom: 11, duration: 800 });
  };

  return (
    <div className="relative w-full h-[380px] sm:h-[480px] rounded-2xl overflow-hidden border border-sagar-border shadow-soft-sm bg-white">
      <div ref={mapContainer} className="w-full h-full" />

      {/* Floating Header Tag */}
      <div className="absolute top-3 left-3 z-10 bg-white/95 backdrop-blur-md border border-sagar-border px-3.5 py-1.5 rounded-xl text-xs flex items-center gap-2 text-sagar-navy shadow-soft-sm font-semibold">
        <Navigation className="w-4 h-4 text-sky-600 shrink-0" />
        <span className="truncate max-w-[200px] sm:max-w-none font-bold">
          {activeCandidate ? activeCandidate.name : <Trans>4D Trajectory & Spatio-Temporal Hazards</Trans>}
        </span>
        <span className="text-[10px] font-mono font-bold text-sky-800 bg-sagar-powder px-2.5 py-0.5 rounded-full border border-sky-200 ml-1 shrink-0">
          <Trans>4D Marine Intelligence</Trans>
        </span>
      </div>

      {/* Floating Nautical Legend & Reset Control */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
        <button
          onClick={handleResetBounds}
          className="bg-white/95 backdrop-blur-md hover:bg-sagar-canvasAlt border border-sagar-border text-sagar-navy px-3 py-1.5 rounded-xl text-xs font-semibold shadow-soft-sm flex items-center gap-1.5 transition-all touch-target cursor-pointer"
          title={t`Reset map view to full voyage`}
        >
          <Maximize2 className="w-3.5 h-3.5 text-sky-600" />
          <span><Trans>Full Voyage</Trans></span>
        </button>

        <div className="hidden sm:flex items-center gap-3 bg-white/95 backdrop-blur-md border border-sagar-border px-3 py-1.5 rounded-xl text-[11px] font-medium text-slate-700 shadow-soft-sm">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-600" />
            <span><Trans>Trajectory</Trans></span>
          </div>
          {pfzZones.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
              <span><Trans>PFZ Zone</Trans></span>
            </div>
          )}
          {hazardFlags.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-pulse" />
              <span><Trans>Hazard Alert</Trans></span>
            </div>
          )}
        </div>
      </div>

      {/* Interactive Floating Marine Decision-Support Tooltip */}
      {tooltip && (
        <div
          className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 px-3.5 py-2.5 rounded-2xl bg-white/98 backdrop-blur-md border border-sagar-border shadow-soft-lg text-sagar-navy text-xs space-y-1 max-w-xs transition-all duration-75"
          style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
        >
          <div className="flex items-center justify-between gap-2 border-b border-sagar-borderLight pb-1.5">
            <span className="font-extrabold text-sagar-navy text-xs truncate">{tooltip.title}</span>
            {tooltip.riskBadge && (
              <span
                className="text-[9px] font-extrabold px-2 py-0.5 rounded-full uppercase tracking-wider shrink-0"
                style={{
                  backgroundColor: tooltip.riskBadge.bg,
                  borderColor: tooltip.riskBadge.border,
                  color: tooltip.riskBadge.color,
                  borderWidth: '1px',
                }}
              >
                {tooltip.riskBadge.text}
              </span>
            )}
          </div>

          {tooltip.subtitle && <p className="text-[11px] text-slate-600 font-medium">{tooltip.subtitle}</p>}

          {tooltip.phase && (
            <div className="text-[11px] text-slate-600 flex items-center justify-between gap-2">
              <span><Trans>Phase:</Trans> <strong className="text-sagar-navy">{tooltip.phase}</strong></span>
              {tooltip.eta && <span><Trans>ETA:</Trans> <strong className="text-sagar-navy">{tooltip.eta} IST</strong></span>}
            </div>
          )}

          {tooltip.coords && (
            <div className="text-[10px] font-mono text-slate-500">{tooltip.coords}</div>
          )}

          {tooltip.hazardDetail && (
            <div className="p-1.5 bg-rose-50 border border-rose-200 rounded-lg text-[10px] text-rose-900 font-semibold leading-snug">
              ⚠️ {tooltip.hazardDetail}
            </div>
          )}

          {tooltip.pfzDetail && (
            <div className="grid grid-cols-3 gap-1 pt-1 text-[10px] font-medium text-slate-700">
              <span className="bg-sagar-canvasAlt px-1.5 py-0.5 rounded text-center">{tooltip.pfzDetail.sst}</span>
              <span className="bg-sagar-canvasAlt px-1.5 py-0.5 rounded text-center">{tooltip.pfzDetail.chlorophyll}</span>
              <span className="bg-emerald-50 text-emerald-800 border border-emerald-200 px-1.5 py-0.5 rounded text-center font-bold">
                {tooltip.pfzDetail.confidence}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

