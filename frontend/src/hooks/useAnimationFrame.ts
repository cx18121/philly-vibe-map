import { useEffect, useRef } from 'react';

export function useAnimationFrame(callback: (dt: number) => void, active: boolean) {
  const cbRef = useRef(callback);
  cbRef.current = callback;

  useEffect(() => {
    if (!active) return;
    let rafId: number;
    let prev = performance.now();
    const loop = (now: number) => {
      const dt = now - prev;
      prev = now;
      cbRef.current(dt);
      rafId = requestAnimationFrame(loop);
    };
    rafId = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(rafId);
  }, [active]);
}
