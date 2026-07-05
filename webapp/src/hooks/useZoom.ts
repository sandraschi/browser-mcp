import { useCallback, useEffect, useState } from 'react';

const ZOOM_LEVELS = [0.8, 1.0, 1.25, 1.5, 2.0, 3.0];

export function useZoom() {
  const [zoomIndex, setZoomIndex] = useState(() => {
    try {
      const saved = localStorage.getItem('tauri-zoom');
      return saved ? ZOOM_LEVELS.indexOf(parseFloat(saved)) : 1;
    } catch { return 1; }
  });

  const applyZoom = useCallback(async (level: number) => {
    localStorage.setItem('tauri-zoom', String(level));
    try {
      const { getCurrentWindow } = await import('@tauri-apps/api/window');
      await (getCurrentWindow() as unknown as { setZoom: (f: number) => Promise<void> }).setZoom(level);
      return;
    } catch {}
    document.documentElement.style.zoom = String(level);
  }, []);

  useEffect(() => {
    const wheelHandler = (e: WheelEvent) => {
      if (!e.ctrlKey) return;
      e.preventDefault();
      setZoomIndex(prev => {
        const next = e.deltaY < 0 ? Math.min(prev + 1, ZOOM_LEVELS.length - 1) : Math.max(prev - 1, 0);
        if (next !== prev) applyZoom(ZOOM_LEVELS[next]);
        return next;
      });
    };

    const keyHandler = (e: KeyboardEvent) => {
      if (!e.ctrlKey) return;
      if (e.key === '=' || e.key === '+') {
        e.preventDefault();
        setZoomIndex(prev => {
          const next = Math.min(prev + 1, ZOOM_LEVELS.length - 1);
          if (next !== prev) applyZoom(ZOOM_LEVELS[next]);
          return next;
        });
      } else if (e.key === '-') {
        e.preventDefault();
        setZoomIndex(prev => {
          const next = Math.max(prev - 1, 0);
          if (next !== prev) applyZoom(ZOOM_LEVELS[next]);
          return next;
        });
      } else if (e.key === '0') {
        e.preventDefault();
        setZoomIndex(1);
        applyZoom(1.0);
      }
    };

    window.addEventListener('wheel', wheelHandler, { passive: false });
    window.addEventListener('keydown', keyHandler);

    const saved = localStorage.getItem('tauri-zoom');
    if (saved) applyZoom(parseFloat(saved));

    return () => {
      window.removeEventListener('wheel', wheelHandler);
      window.removeEventListener('keydown', keyHandler);
    };
  }, [applyZoom]);
}
