import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { useMapStore } from '../store/mapStore';
import { initUrlSync, hydrateFromUrl } from '../lib/urlSync';

describe('urlSync', () => {
  let replaceStateSpy: ReturnType<typeof vi.fn>;
  let unsubscribe: (() => void) | undefined;

  beforeEach(() => {
    // Reset store to defaults
    useMapStore.setState({
      selectedId: null,
      currentYear: 0,
      temporalData: null,
    });

    // Mock history.replaceState
    replaceStateSpy = vi.fn();
    vi.spyOn(window.history, 'replaceState').mockImplementation(replaceStateSpy);

    // Navigate to clean URL (jsdom supports this)
    window.history.pushState = vi.fn();
  });

  afterEach(() => {
    if (unsubscribe) {
      unsubscribe();
      unsubscribe = undefined;
    }
    vi.restoreAllMocks();
  });

  describe('initUrlSync', () => {
    it('updates URL when store selectedId changes', () => {
      unsubscribe = initUrlSync();
      useMapStore.getState().setSelected('042');
      expect(replaceStateSpy).toHaveBeenCalled();
      const lastCall = replaceStateSpy.mock.calls[replaceStateSpy.mock.calls.length - 1];
      expect(lastCall[2]).toContain('nid=042');
    });

    it('updates URL when store currentYear changes', () => {
      unsubscribe = initUrlSync();
      useMapStore.getState().setYear(2022);
      expect(replaceStateSpy).toHaveBeenCalled();
      const lastCall = replaceStateSpy.mock.calls[replaceStateSpy.mock.calls.length - 1];
      expect(lastCall[2]).toContain('year=2022');
    });

    it('writes both params when both are set', () => {
      unsubscribe = initUrlSync();
      useMapStore.getState().setSelected('042');
      useMapStore.getState().setYear(2022);
      const lastCall = replaceStateSpy.mock.calls[replaceStateSpy.mock.calls.length - 1];
      const url = lastCall[2] as string;
      expect(url).toContain('nid=042');
      expect(url).toContain('year=2022');
    });

    it('clears nid param when selection is cleared', () => {
      unsubscribe = initUrlSync();
      useMapStore.getState().setSelected('042');
      useMapStore.getState().clearSelection();
      const lastCall = replaceStateSpy.mock.calls[replaceStateSpy.mock.calls.length - 1];
      const url = lastCall[2] as string;
      expect(url).not.toContain('nid=');
    });
  });

  describe('hydrateFromUrl', () => {
    it('reads nid and year from URL and sets store', () => {
      // Use jsdom's native navigation to set search params
      window.history.replaceState.mockRestore?.();
      window.history.replaceState({}, '', '?nid=042&year=2022');
      hydrateFromUrl();
      const state = useMapStore.getState();
      expect(state.selectedId).toBe('042');
      expect(state.currentYear).toBe(2022);
    });

    it('does nothing when URL has no params', () => {
      window.history.replaceState.mockRestore?.();
      window.history.replaceState({}, '', '/');
      hydrateFromUrl();
      const state = useMapStore.getState();
      expect(state.selectedId).toBeNull();
      expect(state.currentYear).toBe(0);
    });

    it('handles partial params - only nid', () => {
      window.history.replaceState.mockRestore?.();
      window.history.replaceState({}, '', '?nid=042');
      hydrateFromUrl();
      const state = useMapStore.getState();
      expect(state.selectedId).toBe('042');
      expect(state.currentYear).toBe(0);
    });

    it('handles partial params - only year', () => {
      window.history.replaceState.mockRestore?.();
      window.history.replaceState({}, '', '?year=2020');
      hydrateFromUrl();
      const state = useMapStore.getState();
      expect(state.selectedId).toBeNull();
      expect(state.currentYear).toBe(2020);
    });
  });
});
