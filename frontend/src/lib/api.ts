import type { FeatureCollection } from 'geojson';
import type { NeighbourhoodDetail } from './types';

const API_BASE = import.meta.env.VITE_API_URL ?? '';

export async function fetchNeighbourhoods(): Promise<FeatureCollection> {
  const res = await fetch(`${API_BASE}/neighbourhoods`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}

export async function fetchDetail(nid: string): Promise<NeighbourhoodDetail> {
  const res = await fetch(`${API_BASE}/neighbourhoods/${nid}`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
