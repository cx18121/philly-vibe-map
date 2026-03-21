import { create } from 'zustand';
import type { NeighbourhoodDetail } from '../lib/types';

interface MapStore {
  selectedId: string | null;
  hoveredId: string | null;
  isLoading: boolean;
  detail: NeighbourhoodDetail | null;
  setSelected: (id: string | null) => void;
  setHovered: (id: string | null) => void;
  setDetail: (detail: NeighbourhoodDetail | null) => void;
  setLoading: (loading: boolean) => void;
  clearSelection: () => void;
}

export const useMapStore = create<MapStore>((set) => ({
  selectedId: null,
  hoveredId: null,
  isLoading: false,
  detail: null,
  setSelected: (id) => set({ selectedId: id }),
  setHovered: (id) => set({ hoveredId: id }),
  setDetail: (detail) => set({ detail, isLoading: false }),
  setLoading: (loading) => set({ isLoading: loading }),
  clearSelection: () => set({ selectedId: null, detail: null }),
}));
