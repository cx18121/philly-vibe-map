import type { FeatureCollection } from 'geojson';
import type { NeighbourhoodDetail, TemporalData } from './types';

const API_BASE = import.meta.env.VITE_API_URL ?? '/api';

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

export async function fetchTemporal(): Promise<TemporalData> {
  const res = await fetch(`${API_BASE}/temporal`);
  if (!res.ok) throw new Error(`API error: ${res.status}`);
  return res.json();
}
