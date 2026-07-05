import { useCallback, useEffect, useState } from 'react';
import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Bookmarks from './pages/Bookmarks';
import { useConnection } from './store/connection';
import { useZoom } from './hooks/useZoom';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `block px-4 py-2 rounded ${isActive ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`;

const BACKOFF = [1, 2, 4, 8, 16, 30];

export default function App() {
  useZoom();
  const { status, check, setStatus } = useConnection();
  const [attempt, setAttempt] = useState(0);

  const poll = useCallback(() => {
    check();
    setAttempt(prev => Math.min(prev + 1, BACKOFF.length - 1));
  }, [check]);

  useEffect(() => {
    poll();
    const interval = setInterval(poll, BACKOFF[attempt] * 1000);
    return () => clearInterval(interval);
  }, [poll, attempt]);

  useEffect(() => {
    let unlisten: (() => void) | undefined;
    (async () => {
      try {
        const { listen } = await import("@tauri-apps/api/event");
        unlisten = await listen<string>("backend-status", (event) => {
          if (event.payload === "ready") { check(); setAttempt(0); }
          else if (typeof event.payload === "string" && event.payload.startsWith("error:"))
            setStatus("offline");
        });
      } catch { /* not in Tauri */ }
    })();
    return () => { if (unlisten) unlisten(); };
  }, [check, setStatus]);

  return (
    <div className="flex h-screen bg-gray-900 text-gray-100" data-testid="dashboard">
      <nav className="w-56 bg-gray-800 p-4 border-r border-gray-700 flex flex-col">
        <h1 className="text-lg font-bold mb-6 text-indigo-400">Browser MCP</h1>
        <div className="space-y-1 flex-1">
          <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
          <NavLink to="/bookmarks" className={linkClass}>Bookmarks</NavLink>
        </div>
        <div className="flex items-center gap-2 pt-4 border-t border-gray-700">
          <div data-testid="connection-status" className={`w-2 h-2 rounded-full ${status === "connected" ? "bg-green-500" : status === "connecting" ? "bg-yellow-500 animate-pulse" : "bg-red-500"}`} />
          <span data-testid="connection-label" className="text-xs text-gray-500 capitalize">{status}</span>
        </div>
      </nav>
      <main className="flex-1 overflow-auto p-6">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/bookmarks" element={<Bookmarks />} />
        </Routes>
      </main>
    </div>
  );
}
