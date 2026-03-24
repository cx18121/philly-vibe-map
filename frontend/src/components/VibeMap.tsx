import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import { AnimatePresence } from 'framer-motion';
import Map, { Source, Layer, useMap } from 'react-map-gl/maplibre';
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre';
import type { FillLayerSpecification, LineLayerSpecification } from 'maplibre-gl';
import { VIBE_MATCH_EXPR, getInterpolatedColor } from '../lib/colors';
import { BASEMAP_STYLE, INITIAL_VIEW } from '../lib/constants';
import { useMapStore } from '../store/mapStore';
import { useNeighbourhoods } from '../hooks/useNeighbourhoods';
import { useNeighbourhoodDetail } from '../hooks/useNeighbourhoodDetail';
import { useTemporal } from '../hooks/useTemporal';
import MapSkeleton from './MapSkeleton';
import Tooltip from './Tooltip';

const outlineLayer: Omit<LineLayerSpecification, 'source'> = {
  id: 'neighbourhood-outline',
  type: 'line',
  paint: {
    'line-color': '#ffffff',
    'line-width': 1,
    'line-opacity': 0.5,
  },
};

const highlightFillLayer: Omit<FillLayerSpecification, 'source'> = {
  id: 'neighbourhood-highlight',
  type: 'fill',
  paint: {
    'fill-color': '#ffffff',
    'fill-opacity': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      0.18,
      0.0,
    ] as unknown as number,
  },
};

const highlightLineLayer: Omit<LineLayerSpecification, 'source'> = {
  id: 'neighbourhood-highlight-line',
  type: 'line',
  paint: {
    'line-color': '#ffffff',
    'line-width': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      2.5,
      0,
    ] as unknown as number,
    'line-opacity': [
      'case',
      ['boolean', ['feature-state', 'hover'], false],
      0.9,
      0,
    ] as unknown as number,
  },
};

export default function VibeMap() {
  const { geojson, loading, error } = useNeighbourhoods();
  useNeighbourhoodDetail();

  const temporalData = useTemporal();
  // Snap to integer years — color only changes at year boundaries, so recomputing
  // 60 times per year at fractional values burns CPU and triggers MapLibre GPU re-uploads.
  const currentYear = useMapStore((s) => Math.round(s.currentYear));
  const hoveredId = useMapStore((s) => s.hoveredId);
  const setSelected = useMapStore((s) => s.setSelected);
  const setHovered = useMapStore((s) => s.setHovered);
  const clearSelection = useMapStore((s) => s.clearSelection);

  const { current: mapInstance } = useMap();
  const prevHoveredRef = useRef<string | null>(null);

  // Feature-state hover management
  useEffect(() => {
    if (!mapInstance) return;
    const prev = prevHoveredRef.current;
    if (prev !== null) {
      try {
        mapInstance.setFeatureState(
          { source: 'neighbourhoods', id: prev },
          { hover: false },
        );
      } catch {
        // source may not be loaded yet
      }
    }
    if (hoveredId !== null) {
      try {
        mapInstance.setFeatureState(
          { source: 'neighbourhoods', id: hoveredId },
          { hover: true },
        );
      } catch {
        // source may not be loaded yet
      }
    }
    prevHoveredRef.current = hoveredId;
  }, [hoveredId, mapInstance]);

  const [tooltipInfo, setTooltipInfo] = useState<{
    x: number;
    y: number;
    flipX: boolean;
    name: string;
    vibe: string;
  } | null>(null);

  const mapRef = useRef<HTMLDivElement>(null);
  const [focusIndex, setFocusIndex] = useState(-1);

  const neighbourhoodIds = useMemo(
    () =>
      geojson?.features
        .map((f) => f.properties?.NEIGHBORHOOD_NUMBER)
        .filter(Boolean) ?? [],
    [geojson],
  );

  // Compute GeoJSON with temporal fill colours baked in
  const computedGeojson = useMemo(() => {
    if (!geojson) return null;
    if (!temporalData || currentYear <= 0) return geojson;

    return {
      ...geojson,
      features: geojson.features.map((f) => ({
        ...f,
        properties: {
          ...f.properties,
          _fillColor: getInterpolatedColor(
            temporalData,
            f.properties?.NEIGHBORHOOD_NUMBER ?? '',
            currentYear,
          ),
        },
      })),
    };
  }, [geojson, temporalData, currentYear]);

  // Dynamic fill layer spec based on whether temporal data is active
  const fillLayerSpec: Omit<FillLayerSpecification, 'source'> = useMemo(() => ({
    id: 'neighbourhood-fill',
    type: 'fill',
    paint: {
      'fill-color': temporalData
        ? (['get', '_fillColor'] as unknown as string)
        : (VIBE_MATCH_EXPR as unknown as string),
      'fill-opacity': 0.72,
    },
  }), [temporalData]);

  const handleHover = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        const containerWidth = mapRef.current?.clientWidth ?? window.innerWidth;
        setTooltipInfo({
          x: event.point.x,
          y: event.point.y,
          flipX: event.point.x > containerWidth - 220,
          name: feature.properties?.NEIGHBORHOOD_NAME,
          vibe: feature.properties?.dominant_vibe,
        });
        setHovered(feature.properties?.NEIGHBORHOOD_NUMBER);
      } else {
        setTooltipInfo(null);
        setHovered(null);
      }
    },
    [setHovered],
  );

  const handleClick = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        setSelected(feature.properties?.NEIGHBORHOOD_NUMBER);
      }
    },
    [setSelected],
  );

  const handleMouseLeave = useCallback(() => {
    setTooltipInfo(null);
    setHovered(null);
  }, [setHovered]);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        clearSelection();
        setFocusIndex(-1);
        return;
      }
      if (e.key === 'Tab' && mapRef.current?.contains(document.activeElement)) {
        e.preventDefault();
        setFocusIndex((prev) => {
          const next = e.shiftKey
            ? prev <= 0
              ? neighbourhoodIds.length - 1
              : prev - 1
            : (prev + 1) % neighbourhoodIds.length;
          setHovered(neighbourhoodIds[next]);
          return next;
        });
      }
      if (e.key === 'Enter' && focusIndex >= 0) {
        setSelected(neighbourhoodIds[focusIndex]);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [focusIndex, neighbourhoodIds, clearSelection, setHovered, setSelected]);

  if (error && !loading) {
    return (
      <div
        style={{
          width: '100%',
          height: '100vh',
          background: '#0f0f1a',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
        }}
      >
        <p
          style={{
            fontFamily: "'Fraunces', serif",
            fontSize: '1.2rem',
            fontWeight: 700,
            color: 'rgba(240,240,240,0.6)',
            letterSpacing: '-0.02em',
          }}
        >
          Couldn't load the map
        </p>
        <p
          style={{
            fontFamily: "'Outfit', sans-serif",
            fontSize: '0.75rem',
            color: 'rgba(240,240,240,0.28)',
            letterSpacing: '0.04em',
          }}
        >
          Check your connection and refresh the page.
        </p>
      </div>
    );
  }

  if (loading || !computedGeojson) {
    return <MapSkeleton />;
  }

  return (
    <div
      style={{
        width: '100%',
        height: '100vh',
        position: 'relative',
      }}
      tabIndex={0}
      ref={mapRef}
      aria-label="Neighbourhood vibe map. Use Tab to navigate, Enter to select, Escape to close."
    >
      <Map
        initialViewState={INITIAL_VIEW}
        style={{ width: '100%', height: '100%' }}
        mapStyle={BASEMAP_STYLE}
        interactiveLayerIds={['neighbourhood-fill']}
        onMouseMove={handleHover}
        onMouseLeave={handleMouseLeave}
        onClick={handleClick}
      >
        <Source id="neighbourhoods" type="geojson" data={computedGeojson} promoteId="NEIGHBORHOOD_NUMBER">
          <Layer {...fillLayerSpec} />
          <Layer {...highlightFillLayer} />
          <Layer {...highlightLineLayer} />
          <Layer {...outlineLayer} />
        </Source>
      </Map>
      <AnimatePresence>
        {tooltipInfo && <Tooltip key="tooltip" {...tooltipInfo} />}
      </AnimatePresence>
    </div>
  );
}
