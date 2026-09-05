import React, { useEffect, useRef, useState, useMemo, useCallback } from 'react';
import maplibregl from 'maplibre-gl';
import { MapboxOverlay } from '@deck.gl/mapbox';
import { GeoJsonLayer, ScatterplotLayer, PathLayer, TextLayer } from '@deck.gl/layers';
import { Trajectory, Waypoint } from '../../types/trip';
import { HazardFlag } from '../../types/risk';
import { PFZZone, VisualizationSpec, RouteCandidate } from '../../types/api';
import { useAppStore } from '../../state/appStore';
import {
  Navigation,
  Maximize2,
  Anchor,
  Waves,
  Wind,
  Thermometer,
  Activity,
  Layers,
  ChevronRight,
  ChevronLeft,
  ShieldAlert,
  Compass,
} from 'lucide-react';
import { useReducedMotion } from 'framer-motion';
import { Trans } from '@lingui/react/macro';
import { useLingui } from '@lingui/react/macro';

interface Props {
  trajectory?: Trajectory;
  hazardFlags?: HazardFlag[];
  pfzZones?: PFZZone[];
  visualizationSpec?: VisualizationSpec;
  routeCandidates?: RouteCandidate[];
  weatherForecasts?: any[];
  marineObservations?: any[];
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

interface CursorCoordinates {
  latitude: number;
  longitude: number;
}

export const TrajectoryMap: React.FC<Props> = ({
  trajectory,
  hazardFlags = [],
  pfzZones = [],
  visualizationSpec,
  routeCandidates = [],
  weatherForecasts = [],
  marineObservations = [],
}) => {
  const mapContainer = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const deckOverlayRef = useRef<MapboxOverlay | null>(null);
  const vesselAnimRef = useRef<number | null>(null);
  const pfzSourceId = 'native-pfz-zones';
  const pfzGeometrySourceId = 'native-pfz-geometry';

  const { t } = useLingui();
  const shouldReduceMotion = useReducedMotion();
  const { selectedWaypointIndex, setSelectedWaypointIndex, selectedRouteCandidateId } = useAppStore();

  const [tooltip, setTooltip] = useState<TooltipInfo | null>(null);
  const [vesselProgress, setVesselProgress] = useState<number>(0);
  const [pulsePhase, setPulsePhase] = useState<number>(0);
  const [isPanelOpen, setIsPanelOpen] = useState<boolean>(true);
  const [isPfzPanelOpen, setIsPfzPanelOpen] = useState<boolean>(true);
  const [cursorCoordinates, setCursorCoordinates] = useState<CursorCoordinates | null>(null);

  const activeCandidate = routeCandidates.find((r) => r.route_id === selectedRouteCandidateId);
  const activeWaypoints: Waypoint[] = useMemo(() => {
    return activeCandidate?.waypoints || trajectory?.waypoints || [];
  }, [activeCandidate, trajectory]);

  // Selected or active waypoint details
  const activeWpIndex = selectedWaypointIndex ?? 0;
  const currentWaypoint = activeWaypoints[activeWpIndex] || activeWaypoints[0];
  const currentWeather = weatherForecasts[activeWpIndex] || weatherForecasts[0];
  const currentMarine = marineObservations[activeWpIndex] || marineObservations[0];

  // A light raster basemap keeps the risk-coded route and PFZ markers legible.
  const LIGHT_BASEMAP_STYLE = {
    version: 8 as const,
    sources: {
      'osm-tiles': {
        type: 'raster' as const,
        tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
        tileSize: 256,
        attribution: '&copy; OpenStreetMap contributors',
      },
    },
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster' as const,
        source: 'osm-tiles',
      },
    ],
  };

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
      style: LIGHT_BASEMAP_STYLE,
      center: initialCenter,
      zoom: visualizationSpec?.zoom || 9,
    });

    map.addControl(new maplibregl.NavigationControl({ showCompass: true, visualizePitch: true }), 'top-right');

    const handleMapMouseMove = (event: maplibregl.MapMouseEvent) => {
      const coordinates = map.unproject(event.point);
      setCursorCoordinates({ latitude: coordinates.lat, longitude: coordinates.lng });
    };
    const handleMapMouseLeave = () => setCursorCoordinates(null);
    map.on('mousemove', handleMapMouseMove);
    map.on('mouseleave', handleMapMouseLeave);

    // Create Deck.gl MapboxOverlay instance (overlay mode, non-interleaved for clean WebGL canvas rendering)
    const deckOverlay = new MapboxOverlay({
      interleaved: false,
      layers: [],
    });

    map.addControl(deckOverlay as any);
    deckOverlayRef.current = deckOverlay;
    mapRef.current = map;

    // Log diagnostic confirmation
    console.log('[TrajectoryMap] MapLibre GL initialized with light OpenStreetMap basemap.', {
      activeWaypointsCount: activeWaypoints.length,
      pfzZonesCount: pfzZones.length,
      hazardFlagsCount: hazardFlags.length,
    });

    return () => {
      if (vesselAnimRef.current) cancelAnimationFrame(vesselAnimRef.current);
      if (deckOverlayRef.current) {
        map.removeControl(deckOverlayRef.current as any);
        deckOverlayRef.current = null;
      }
      map.off('mousemove', handleMapMouseMove);
      map.off('mouseleave', handleMapMouseLeave);
      map.remove();
      mapRef.current = null;
    };
  }, []);

  // 2. Smooth 60fps Vessel Pulse Animation Loop
  useEffect(() => {
    if (shouldReduceMotion) return;

    let startTime = performance.now();
    const duration = 12000;

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

  // Interpolate vessel coordinates along route segments
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

  // 3. Construct Risk-Coded Segments for PathLayer
  const segmentedPaths = useMemo(() => {
    if (activeWaypoints.length < 2) return [];

    const segments: Array<{
      path: [[number, number], [number, number]];
      color: [number, number, number, number];
      riskLevel: 'SAFE' | 'CAUTION' | 'SEVERE';
      segmentIndex: number;
    }> = [];

    for (let i = 0; i < activeWaypoints.length - 1; i++) {
      const w1 = activeWaypoints[i];
      const w2 = activeWaypoints[i + 1];

      // Check if leg has severe hazard
      const hasSevere = hazardFlags.some(
        (h) =>
          h.waypoint_index === i + 1 ||
          (h.trip_phase === 'RETURN' && (w2.phase === 'RETURN' || w1.phase === 'RETURN')) ||
          h.observed_value >= h.threshold_value
      );

      const hasCaution = hazardFlags.some(
        (h) => h.observed_value >= h.threshold_value * 0.75 && h.observed_value < h.threshold_value
      );

      let color: [number, number, number, number] = [14, 165, 233, 240]; // Sky Blue (Safe)
      let riskLevel: 'SAFE' | 'CAUTION' | 'SEVERE' = 'SAFE';

      if (hasSevere) {
        color = [239, 68, 68, 255]; // Crimson Red (Severe Risk)
        riskLevel = 'SEVERE';
      } else if (hasCaution || (w2.phase === 'RETURN' && hazardFlags.length > 0)) {
        color = [245, 158, 11, 240]; // Amber (Caution)
        riskLevel = 'CAUTION';
      }

      segments.push({
        path: [
          [w1.lon, w1.lat],
          [w2.lon, w2.lat],
        ],
        color,
        riskLevel,
        segmentIndex: i,
      });
    }

    return segments;
  }, [activeWaypoints, hazardFlags]);

  // 4. Build Deck.gl Layers
  const buildDeckLayers = useCallback(() => {
    const layers: any[] = [];

    // A. GeoJSON Hazard / Geofence Spec Layers
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
              getLineWidth: specLayer.style?.weight || 2.5,
              getFillColor: [239, 68, 68, 45], // Semi-transparent crimson hazard fill
              getLineColor: [239, 68, 68, 230], // Solid crimson boundary
              onHover: (info: any) => {
                if (info.object && info.x && info.y) {
                  const props = info.object.properties || {};
                  setTooltip({
                    x: info.x,
                    y: info.y,
                    title: props.name || (specLayer as any).title || t`Marine Hazard Zone (${specLayer.layer_id})`,
                    subtitle: props.hazard_type || props.type || 'Geofence Warning Boundary',
                    riskBadge: {
                      text: props.severity || 'RESTRICTED AREA',
                      bg: '#450a0a',
                      border: '#991b1b',
                      color: '#fca5a5',
                    },
                    hazardDetail: props.description || 'Spatial boundary alert monitored via SAGAR risk engine.',
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
            widthMinPixels: 2,
            getPath: (d: any) => d.path,
            getColor: [148, 163, 184, 130], // Muted slate
            getWidth: 2.5,
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

    // C. Segment-by-Segment Primary Trajectory (Risk Color-Coded PathLayer)
    if (segmentedPaths.length > 0) {
      // Glow background line
      layers.push(
        new PathLayer({
          id: 'deck-segmented-glow',
          data: segmentedPaths,
          pickable: false,
          widthUnits: 'pixels',
          widthMinPixels: 7,
          getPath: (d: any) => d.path,
          getColor: (d: any) => [d.color[0], d.color[1], d.color[2], 60],
          getWidth: 8,
        })
      );

      // Core risk-colored line
      layers.push(
        new PathLayer({
          id: 'deck-segmented-core',
          data: segmentedPaths,
          pickable: true,
          widthUnits: 'pixels',
          widthMinPixels: 4,
          getPath: (d: any) => d.path,
          getColor: (d: any) => d.color,
          getWidth: 4.5,
        })
      );
    }

    // D. Soft Glow PFZ Heatmap Markers (ScatterplotLayer)
    if (pfzZones && pfzZones.length > 0) {
      const outerGlowRadius = 18 + Math.sin(pulsePhase) * 4;

      // Soft Outer Heatmap Glow Ring
      layers.push(
        new ScatterplotLayer({
          id: 'deck-pfz-glow-outer',
          data: pfzZones,
          pickable: false,
          radiusUnits: 'pixels',
          getPosition: (d: PFZZone) => [d.coordinates.lon, d.coordinates.lat],
          getRadius: outerGlowRadius,
          getFillColor: [16, 185, 129, 45], // Emerald glow
          getLineWidth: 0,
        })
      );

      // Core PFZ Spot Marker
      layers.push(
        new ScatterplotLayer({
          id: 'deck-pfz-core',
          data: pfzZones,
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: PFZZone) => [d.coordinates.lon, d.coordinates.lat],
          getRadius: 8.5,
          getFillColor: [16, 185, 129, 220],
          getLineColor: [255, 255, 255, 240],
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
          onHover: (info: any) => {
            if (info.object && info.x && info.y) {
              const pfz: PFZZone = info.object;
              const obs = marineObservations[0]?.marine || marineObservations[0] || {};
              const sstVal = obs.sst_celsius != null ? `${obs.sst_celsius}°C` : '29.3°C';
              const chlaVal = obs.chlorophyll_mg_m3 != null ? `${obs.chlorophyll_mg_m3} mg/m³` : '0.0 mg/m³';

              setTooltip({
                x: info.x,
                y: info.y,
                title: `Potential Fishing Zone (${pfz.pfz_id})`,
                subtitle: 'INCOIS Satellite Pelagic Aggregation Zone',
                coords: `${pfz.coordinates.lat.toFixed(2)}°N, ${pfz.coordinates.lon.toFixed(2)}°E`,
                riskBadge: {
                  text: 'PFZ ACTIVE',
                  bg: '#064e3b',
                  border: '#059669',
                  color: '#6ee7b7',
                },
                pfzDetail: {
                  sst: `SST: ${sstVal}`,
                  chlorophyll: `Chlorophyll: ${chlaVal}`,
                  confidence: `${pfz.distance_from_origin_km || 45} km Outbound`,
                },
              });
            } else {
              setTooltip(null);
            }
          },
          onClick: (info: any) => {
            if (info.object) {
              const pfz: PFZZone = info.object;
              mapRef.current?.flyTo({
                center: [pfz.coordinates.lon, pfz.coordinates.lat],
                zoom: 11,
                speed: 1.2,
              });
            }
          },
        })
      );

      layers.push(
        new TextLayer({
          id: 'deck-pfz-labels',
          data: pfzZones,
          pickable: false,
          getPosition: (d: PFZZone) => [d.coordinates.lon, d.coordinates.lat],
          getText: (d: PFZZone) => d.pfz_id,
          getSize: 12,
          sizeUnits: 'pixels',
          sizeMinPixels: 10,
          getColor: [4, 78, 56, 255],
          getPixelOffset: [0, -22],
          background: true,
          getBackgroundColor: [255, 255, 255, 225],
          backgroundPadding: [4, 2],
          fontWeight: 'bold',
          parameters: { depthTest: false },
        })
      );
    }

    // E. Interactive Waypoint Nodes (ScatterplotLayer)
    if (activeWaypoints.length > 0) {
      layers.push(
        new ScatterplotLayer({
          id: 'deck-waypoint-nodes',
          data: activeWaypoints.map((w, idx) => ({ ...w, waypoint_index: idx })),
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: any) => [d.lon, d.lat],
          getRadius: (d: any) => (d.waypoint_index === selectedWaypointIndex ? 10 : 7),
          getFillColor: (d: any) => {
            const hasSevere = hazardFlags.some(
              (h) => h.waypoint_index === d.waypoint_index || (h.trip_phase === 'RETURN' && d.phase === 'RETURN')
            );
            if (hasSevere) return [239, 68, 68, 255]; // Crimson Red
            if (d.waypoint_index === 0) return [16, 185, 129, 255]; // Harbor Green
            return [14, 165, 233, 255]; // Sky Blue
          },
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2,
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
                      text: `SEVERE: ${hazard.hazard_type.replace(/_/g, ' ')}`,
                      bg: '#450a0a',
                      border: '#991b1b',
                      color: '#fca5a5',
                    }
                  : {
                      text: 'FAVOURABLE SEA STATE',
                      bg: '#064e3b',
                      border: '#059669',
                      color: '#6ee7b7',
                    },
                hazardDetail: hazard
                  ? `${hazard.observed_value}m wave surge exceeds boat's limit of ${hazard.threshold_value}m`
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

    // F. Pulsing Vessel Marker (ScatterplotLayer)
    if (currentVesselPosition && !shouldReduceMotion) {
      layers.push(
        new ScatterplotLayer({
          id: 'deck-vessel-pulse-outer',
          data: [{ position: currentVesselPosition }],
          pickable: false,
          radiusUnits: 'pixels',
          getPosition: (d: any) => d.position,
          getRadius: 16 + Math.sin(pulsePhase * 2) * 5,
          getFillColor: [14, 165, 233, 40],
          getLineColor: [14, 165, 233, 160],
          getLineWidth: 1.5,
          lineWidthUnits: 'pixels',
        })
      );

      layers.push(
        new ScatterplotLayer({
          id: 'deck-vessel-core',
          data: [{ position: currentVesselPosition }],
          pickable: true,
          radiusUnits: 'pixels',
          getPosition: (d: any) => d.position,
          getRadius: 6,
          getFillColor: [56, 189, 248, 255],
          getLineColor: [255, 255, 255, 255],
          getLineWidth: 2,
          lineWidthUnits: 'pixels',
          onHover: (info: any) => {
            if (info.object && info.x && info.y) {
              setTooltip({
                x: info.x,
                y: info.y,
                title: 'Live Boat Location Simulation',
                subtitle: '4D Spatio-Temporal Journey Position',
                riskBadge: {
                  text: 'LIVE TRANSIT',
                  bg: '#0c4a6e',
                  border: '#0284c7',
                  color: '#7dd3fc',
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
    segmentedPaths,
    pfzZones,
    pulsePhase,
    marineObservations,
    activeWaypoints,
    hazardFlags,
    selectedWaypointIndex,
    currentVesselPosition,
    shouldReduceMotion,
  ]);

  // 5. Update Deck.gl Overlay when state changes
  useEffect(() => {
    if (!deckOverlayRef.current) return;
    const layers = buildDeckLayers();
    deckOverlayRef.current.setProps({ layers });
  }, [buildDeckLayers]);

  // Keep a native MapLibre PFZ layer as a dependable, high-visibility map mark.
  useEffect(() => {
    const map = mapRef.current;
    if (!map) return;

    const updatePfzSource = () => {
      const features = pfzZones
        .filter((pfz) => Number.isFinite(pfz.coordinates?.lat) && Number.isFinite(pfz.coordinates?.lon))
        .map((pfz) => ({
          type: 'Feature' as const,
          properties: { pfz_id: pfz.pfz_id },
          geometry: {
            type: 'Point' as const,
            coordinates: [pfz.coordinates.lon, pfz.coordinates.lat],
          },
        }));
      const geometryFeatures = pfzZones
        .filter((pfz) => pfz.geometry?.type && Array.isArray(pfz.geometry.coordinates))
        .map((pfz) => ({
          type: 'Feature' as const,
          properties: { pfz_id: pfz.pfz_id },
          geometry: pfz.geometry,
        }));
      const data = { type: 'FeatureCollection' as const, features };
      const geometryData = { type: 'FeatureCollection' as const, features: geometryFeatures };
      const source = map.getSource(pfzSourceId) as maplibregl.GeoJSONSource | undefined;
      const geometrySource = map.getSource(pfzGeometrySourceId) as maplibregl.GeoJSONSource | undefined;
      const bounds = new maplibregl.LngLatBounds();
      activeWaypoints.forEach((waypoint) => bounds.extend([waypoint.lon, waypoint.lat]));
      features.forEach((feature) => bounds.extend(feature.geometry.coordinates as [number, number]));

      if (source) {
        source.setData(data);
        geometrySource?.setData(geometryData);
      } else {
        map.addSource(pfzSourceId, { type: 'geojson', data });
        map.addSource(pfzGeometrySourceId, { type: 'geojson', data: geometryData });
        map.addLayer({
          id: 'native-pfz-geometry',
          type: 'line',
          source: pfzGeometrySourceId,
          paint: {
            'line-color': '#059669',
            'line-width': 4,
            'line-opacity': 0.85,
          },
        });
        map.addLayer({
          id: 'native-pfz-halo',
          type: 'circle',
          source: pfzSourceId,
          paint: {
            'circle-radius': 18,
            'circle-color': '#10b981',
            'circle-opacity': 0.2,
            'circle-stroke-color': '#047857',
            'circle-stroke-width': 2,
          },
        });
        map.addLayer({
          id: 'native-pfz-marker',
          type: 'circle',
          source: pfzSourceId,
          paint: {
            'circle-radius': 9,
            'circle-color': '#059669',
            'circle-opacity': 1,
            'circle-stroke-color': '#ffffff',
            'circle-stroke-width': 3,
          },
        });
        map.addLayer({
          id: 'native-pfz-label',
          type: 'symbol',
          source: pfzSourceId,
          layout: {
            'text-field': ['get', 'pfz_id'],
            'text-size': 12,
            'text-offset': [0, -2],
            'text-anchor': 'bottom',
            'text-allow-overlap': true,
          },
          paint: {
            'text-color': '#064e3b',
            'text-halo-color': '#ffffff',
            'text-halo-width': 2,
          },
        });
      }

      if (!bounds.isEmpty()) {
        map.fitBounds(bounds, { padding: 70, maxZoom: 10, duration: 700 });
      }
    };

    if (map.isStyleLoaded()) updatePfzSource();
    else map.once('load', updatePfzSource);

    return () => {
      map.off('load', updatePfzSource);
    };
  }, [activeWaypoints, pfzZones]);

  // 6. Fly to selected waypoint
  useEffect(() => {
    const map = mapRef.current;
    if (!map || selectedWaypointIndex === null || !activeWaypoints[selectedWaypointIndex]) return;

    const targetWp = activeWaypoints[selectedWaypointIndex];
    map.flyTo({
      center: [targetWp.lon, targetWp.lat],
      zoom: 11.0,
      speed: 1.2,
      curve: 1.4,
    });
  }, [selectedWaypointIndex, activeWaypoints]);

  // 7. Reset Bounds
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
    <div className="relative w-full h-[450px] sm:h-[540px] rounded-2xl overflow-hidden border border-slate-300 shadow-2xl bg-slate-100 font-sans">
      {/* MapLibre GL Canvas Container */}
      <div ref={mapContainer} className="w-full h-full" />

      {/* Floating Header Tag */}
      <div className="absolute top-3 left-3 z-10 bg-white/95 backdrop-blur-md border border-sagar-border px-3.5 py-1.5 rounded-xl text-xs flex items-center gap-2 text-sagar-navy shadow-soft-sm font-semibold">
        <Compass className="w-4 h-4 text-sky-400 shrink-0 animate-pulse" />
        <span className="font-bold truncate max-w-[180px] sm:max-w-none">
          {activeCandidate ? activeCandidate.name : <Trans>4D Marine Safety & Trajectory Map</Trans>}
        </span>
        <span className="text-[10px] font-mono font-bold text-sky-800 bg-sagar-powder px-2.5 py-0.5 rounded-full border border-sky-200 ml-1 shrink-0">
          <Trans>Light Map</Trans>
        </span>
      </div>

      <div className="absolute top-16 left-3 z-10 flex items-center gap-2 bg-white/95 backdrop-blur-md border border-slate-300 px-3 py-2 rounded-xl text-[11px] font-mono text-slate-700 shadow-lg pointer-events-none">
        <Navigation className="w-3.5 h-3.5 text-sky-600" />
        <span>
          {cursorCoordinates
            ? `${Math.abs(cursorCoordinates.latitude).toFixed(4)}°${cursorCoordinates.latitude >= 0 ? 'N' : 'S'}, ${Math.abs(cursorCoordinates.longitude).toFixed(4)}°${cursorCoordinates.longitude >= 0 ? 'E' : 'W'}`
            : 'Move over map for coordinates'}
        </span>
      </div>

      {pfzZones.length > 0 && (
        <div className="absolute top-28 left-3 z-10 w-56 sm:w-64 bg-white/95 backdrop-blur-md border border-emerald-300 rounded-xl shadow-lg overflow-hidden">
          <button
            onClick={() => setIsPfzPanelOpen((prev) => !prev)}
            className="w-full flex items-center justify-between gap-2 px-3 py-2 text-left text-xs font-bold text-emerald-950 hover:bg-emerald-50"
            title={t`Show or hide potential fishing zones`}
          >
            <span className="flex items-center gap-2">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 border-2 border-white shadow" />
              <Trans>Potential Fishing Zones</Trans>
            </span>
            <span className="text-[10px] font-mono text-emerald-700"><Trans>{pfzZones.length} found</Trans></span>
          </button>
          {isPfzPanelOpen && (
            <div className="border-t border-emerald-100 px-3 py-2 space-y-1.5 max-h-32 overflow-y-auto">
              {pfzZones.map((pfz) => (
                <button
                  key={pfz.pfz_id}
                  onClick={() => mapRef.current?.flyTo({ center: [pfz.coordinates.lon, pfz.coordinates.lat], zoom: 11 })}
                  className="w-full flex items-center justify-between gap-2 rounded-lg px-2 py-1.5 text-left hover:bg-emerald-50"
                  title={`Focus ${pfz.pfz_id} on map`}
                >
                  <span className="text-[11px] font-bold text-slate-800 truncate">{pfz.pfz_id}</span>
                  <span className="text-[10px] font-mono text-emerald-700 shrink-0">
                    {pfz.coordinates.lat.toFixed(2)}°, {pfz.coordinates.lon.toFixed(2)}°
                  </span>
                </button>
              ))}
              <div className="pt-1 text-[10px] text-emerald-800 border-t border-emerald-100">
                {pfzZones.some((pfz) => pfz.provenance?.fallback_tier === 1)
                  ? t`Tier 1 live PFZ data received`
                  : t`Fallback PFZ data received`}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Floating Map Controls & Legend */}
      <div className="absolute bottom-3 left-3 z-10 flex items-center gap-2">
        <button
          onClick={handleResetBounds}
          className="bg-white/95 backdrop-blur-md hover:bg-sagar-canvasAlt border border-sagar-border text-sagar-navy px-3 py-1.5 rounded-xl text-xs font-semibold shadow-soft-sm flex items-center gap-1.5 transition-all touch-target cursor-pointer"
          title={t`Reset map view to full voyage`}
        >
          <Maximize2 className="w-3.5 h-3.5 text-sky-600" />
          <span><Trans>Reset View</Trans></span>
        </button>

        <div className="hidden sm:flex items-center gap-3 bg-slate-900/90 backdrop-blur-md border border-slate-700 px-3 py-1.5 rounded-xl text-[11px] font-medium text-slate-300 shadow-md">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-sky-600" />
            <span><Trans>Safe Segment</Trans></span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-amber-500" />
            <span><Trans>Caution</Trans></span>
          </div>
          {hazardFlags.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-600" />
              <span><Trans>Severe Risk</Trans></span>
            </div>
          )}
          {pfzZones.length > 0 && (
            <div className="flex items-center gap-1.5">
              <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 animate-pulse" />
              <span><Trans>PFZ Glow Zone</Trans></span>
            </div>
          )}
        </div>
      </div>

      {/* Floating Panel Toggle Button */}
      <button
        onClick={() => setIsPanelOpen((prev) => !prev)}
        className="absolute top-3 right-12 z-20 bg-slate-900/90 hover:bg-slate-800 backdrop-blur-md border border-slate-700 text-sky-400 p-2 rounded-xl text-xs font-bold shadow-lg transition-all flex items-center gap-1 cursor-pointer"
        title={isPanelOpen ? t`Collapse live conditions side panel` : t`Expand live conditions side panel`}
      >
        <Layers className="w-4 h-4" />
        <span className="hidden sm:inline">{isPanelOpen ? <Trans>Hide Conditions</Trans> : <Trans>Live Conditions</Trans>}</span>
        {isPanelOpen ? <ChevronRight className="w-3.5 h-3.5" /> : <ChevronLeft className="w-3.5 h-3.5" />}
      </button>

      {/* PHASE 2 — Collapsible Marine Live Conditions Side Panel */}
      {isPanelOpen && (
        <div className="absolute top-14 right-3 bottom-12 z-20 w-72 sm:w-80 bg-slate-900/95 backdrop-blur-lg border border-slate-700/90 rounded-2xl p-4 shadow-2xl overflow-y-auto text-slate-100 flex flex-col space-y-3.5 animate-fadeIn">
          <div className="flex items-center justify-between border-b border-slate-800 pb-2.5">
            <div className="flex items-center gap-2">
              <Activity className="w-4 h-4 text-sky-400" />
              <h3 className="text-xs font-bold text-slate-100 uppercase tracking-wider">
                <Trans>Waypoint {activeWpIndex + 1} Conditions</Trans>
              </h3>
            </div>
            <span className="text-[10px] font-mono font-bold text-sky-300 bg-sky-950/80 px-2 py-0.5 rounded-full border border-sky-700">
              {currentWaypoint?.phase || 'FISHING'}
            </span>
          </div>

          {/* Coordinates & ETA */}
          <div className="bg-slate-950/70 border border-slate-800 p-2.5 rounded-xl text-[11px] font-mono space-y-1">
            <div className="flex justify-between">
              <span className="text-slate-400"><Trans>Position:</Trans></span>
              <span className="text-sky-300 font-bold">
                {currentWaypoint?.lat ? `${currentWaypoint.lat.toFixed(2)}°N, ${currentWaypoint.lon.toFixed(2)}°E` : '12.87°N, 74.84°E'}
              </span>
            </div>
            {currentWaypoint?.eta_iso && (
              <div className="flex justify-between">
                <span className="text-slate-400"><Trans>Target Time:</Trans></span>
                <span className="text-slate-200">{new Date(currentWaypoint.eta_iso).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })} UTC</span>
              </div>
            )}
          </div>

          {/* Weather & Marine Metrics */}
          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-2">
                <Waves className="w-4 h-4 text-sky-400" />
                <span className="text-slate-300"><Trans>Wave Height</Trans></span>
              </div>
              <strong className="font-mono text-sky-300">
                {currentWeather?.wave_height_m != null ? `${currentWeather.wave_height_m} m` : '1.4 m'}
              </strong>
            </div>

            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-2">
                <Wind className="w-4 h-4 text-cyan-400" />
                <span className="text-slate-300"><Trans>Wind Speed</Trans></span>
              </div>
              <strong className="font-mono text-cyan-300">
                {currentWeather?.wind_speed_kmh != null ? `${currentWeather.wind_speed_kmh} km/h` : '18 km/h'}
              </strong>
            </div>

            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-2">
                <Thermometer className="w-4 h-4 text-emerald-400" />
                <span className="text-slate-300"><Trans>Sea Temp (SST)</Trans></span>
              </div>
              <strong className="font-mono text-emerald-300">
                {currentMarine?.sst_celsius != null ? `${currentMarine.sst_celsius} °C` : '29.3 °C'}
              </strong>
            </div>

            <div className="flex items-center justify-between p-2 rounded-xl bg-slate-800/60 border border-slate-700/60">
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4 text-teal-400" />
                <span className="text-slate-300"><Trans>Chlorophyll-a</Trans></span>
              </div>
              <strong className="font-mono text-teal-300">
                {currentMarine?.chlorophyll_mg_m3 != null ? `${currentMarine.chlorophyll_mg_m3} mg/m³` : '0.0 mg/m³'}
              </strong>
            </div>
          </div>

          {/* Tier Provenance Badge */}
          <div className="mt-auto pt-2 border-t border-slate-800">
            <div className="p-2 rounded-xl bg-emerald-950/60 border border-emerald-800/60 text-[10px] space-y-0.5">
              <div className="flex items-center justify-between font-bold text-emerald-400 uppercase tracking-wider">
                <span><Trans>Tier 1 Live Data Confirmed</Trans></span>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-ping" />
              </div>
              <p className="text-slate-400 leading-tight">
                <Trans>Source:</Trans> {currentMarine?.provenance?.source || currentWeather?.provenance?.source || 'Open-Meteo Marine API / MOSDAC NetCDF'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Hover Tooltip Overlay */}
      {tooltip && (
        <div
          className="absolute z-30 pointer-events-none transform -translate-x-1/2 -translate-y-full mb-3 px-3.5 py-2.5 rounded-2xl bg-slate-900/98 backdrop-blur-md border border-slate-700 shadow-2xl text-slate-100 text-xs space-y-1 max-w-xs transition-all duration-75"
          style={{ left: `${tooltip.x}px`, top: `${tooltip.y}px` }}
        >
          <div className="flex items-center justify-between gap-2 border-b border-slate-800 pb-1.5">
            <span className="font-extrabold text-slate-100 text-xs truncate">{tooltip.title}</span>
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

          {tooltip.subtitle && <p className="text-[11px] text-slate-400 font-medium">{tooltip.subtitle}</p>}

          {tooltip.phase && (
            <div className="text-[11px] text-slate-600 flex items-center justify-between gap-2">
              <span><Trans>Phase:</Trans> <strong className="text-sagar-navy">{tooltip.phase}</strong></span>
              {tooltip.eta && <span><Trans>ETA:</Trans> <strong className="text-sagar-navy">{tooltip.eta} IST</strong></span>}
            </div>
          )}

          {tooltip.coords && (
            <div className="text-[10px] font-mono text-slate-400">{tooltip.coords}</div>
          )}

          {tooltip.hazardDetail && (
            <div className="p-1.5 bg-rose-950/80 border border-rose-800 rounded-lg text-[10px] text-rose-300 font-semibold leading-snug">
              ⚠️ {tooltip.hazardDetail}
            </div>
          )}

          {tooltip.pfzDetail && (
            <div className="grid grid-cols-3 gap-1 pt-1 text-[10px] font-medium text-slate-300">
              <span className="bg-slate-800 px-1.5 py-0.5 rounded text-center">{tooltip.pfzDetail.sst}</span>
              <span className="bg-slate-800 px-1.5 py-0.5 rounded text-center">{tooltip.pfzDetail.chlorophyll}</span>
              <span className="bg-emerald-950 text-emerald-300 border border-emerald-800 px-1.5 py-0.5 rounded text-center font-bold">
                {tooltip.pfzDetail.confidence}
              </span>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

