import { useState, useCallback, useRef, useMemo, useEffect } from 'react';
import Map, { Source, Layer } from 'react-map-gl/maplibre';
import type { MapLayerMouseEvent } from 'react-map-gl/maplibre';
import type { FillLayerSpecification, LineLayerSpecification } from 'maplibre-gl';
import { VIBE_MATCH_EXPR } from '../lib/colors';
import { BASEMAP_STYLE, INITIAL_VIEW } from '../lib/constants';
import { useMapStore } from '../store/mapStore';
import { useNeighbourhoods } from '../hooks/useNeighbourhoods';
import { useNeighbourhoodDetail } from '../hooks/useNeighbourhoodDetail';
import MapSkeleton from './MapSkeleton';
import Tooltip from './Tooltip';

const fillLayer: Omit<FillLayerSpecification, 'source'> = {
  id: 'neighbourhood-fill',
  type: 'fill',
  paint: {
    'fill-color': VIBE_MATCH_EXPR as unknown as string,
    'fill-opacity': 0.6,
  },
};

const outlineLayer: Omit<LineLayerSpecification, 'source'> = {
  id: 'neighbourhood-outline',
  type: 'line',
  paint: {
    'line-color': '#ffffff',
    'line-width': 1,
    'line-opacity': 0.5,
  },
};

export default function VibeMap() {
  const { geojson, loading } = useNeighbourhoods();
  useNeighbourhoodDetail();

  const setSelected = useMapStore((s) => s.setSelected);
  const setHovered = useMapStore((s) => s.setHovered);
  const clearSelection = useMapStore((s) => s.clearSelection);

  const [tooltipInfo, setTooltipInfo] = useState<{
    x: number;
    y: number;
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

  const handleHover = useCallback(
    (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      if (feature) {
        setTooltipInfo({
          x: event.point.x,
          y: event.point.y,
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

  if (loading || !geojson) {
    return <MapSkeleton />;
  }

  return (
    <div
      style={{ width: '100%', height: '100vh', position: 'relative' }}
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
        <Source id="neighbourhoods" type="geojson" data={geojson}>
          <Layer {...fillLayer} />
          <Layer {...outlineLayer} />
        </Source>
      </Map>
      {tooltipInfo && <Tooltip {...tooltipInfo} />}
    </div>
  );
}
