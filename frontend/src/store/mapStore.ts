import { create } from 'zustand';
import type { NeighbourhoodDetail, TemporalData } from '../lib/types';

interface MapStore {
  selectedId: string | null;
  hoveredId: string | null;
  isLoading: boolean;
  detail: NeighbourhoodDetail | null;
  detailError: boolean;
  detailFetchKey: number;
  setSelected: (id: string | null) => void;
  setHovered: (id: string | null) => void;
  setDetail: (detail: NeighbourhoodDetail | null) => void;
  setLoading: (loading: boolean) => void;
  setDetailError: (err: boolean) => void;
  retryDetailFetch: () => void;
  clearSelection: () => void;

  // Temporal state
  currentYear: number;
  isPlaying: boolean;
  temporalData: TemporalData | null;
  availableYears: number[];
  setYear: (year: number) => void;
  togglePlay: () => void;
  setTemporalData: (data: TemporalData) => void;
}

export const useMapStore = create<MapStore>((set) => ({
  selectedId: null,
  hoveredId: null,
  isLoading: false,
  detail: null,
  detailError: false,
  detailFetchKey: 0,
  setSelected: (id) => set({ selectedId: id }),
  setHovered: (id) => set({ hoveredId: id }),
  setDetail: (detail) => set({ detail, isLoading: false }),
  setLoading: (loading) => set({ isLoading: loading }),
  setDetailError: (err) => set({ detailError: err, isLoading: false }),
  retryDetailFetch: () => set((s) => ({ detailFetchKey: s.detailFetchKey + 1, detailError: false })),
  clearSelection: () => set({ selectedId: null, detail: null, detailError: false }),

  // Temporal state
  currentYear: 0,
  isPlaying: false,
  temporalData: null,
  availableYears: [],
  setYear: (year) => set({ currentYear: year }),
  togglePlay: () => set((state) => ({ isPlaying: !state.isPlaying })),
  setTemporalData: (data) => {
    const firstEntry = Object.values(data)[0];
    const years = firstEntry
      ? Object.keys(firstEntry).map(Number).sort((a, b) => a - b)
      : [];
    set({
      temporalData: data,
      availableYears: years,
      currentYear: years.length > 0 ? years[years.length - 1] : 0,
    });
  },
}));
