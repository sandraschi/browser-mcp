import { useEffect, useState } from 'react';
import { Route, Routes, useNavigate } from 'react-router-dom';
import HelpModal from './components/layout/HelpModal';
import Sidebar from './components/layout/Sidebar';
import Topbar from './components/layout/Topbar';
import { useZoom } from './hooks/useZoom';
import ApiDocs from './pages/ApiDocs';
import Apps from './pages/Apps';
import Bookmarks from './pages/Bookmarks';
import Chat from './pages/Chat';
import Dashboard from './pages/Dashboard';
import Help from './pages/Help';
import Logs from './pages/Logs';
import Settings from './pages/Settings';
import Skills from './pages/Skills';
import Tools from './pages/Tools';

export default function App() {
  useZoom();
  const navigate = useNavigate();
  const [sidebar, setSidebar] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (!e.ctrlKey || e.altKey) return;
      if (e.key === 'l' || e.key === 'L') {
        e.preventDefault();
        navigate('/logs');
      } else if (e.key === 'h' || e.key === 'H') {
        e.preventDefault();
        setShowHelp((v) => !v);
      }
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [navigate]);

  return (
    <div className="h-screen flex flex-col bg-zinc-950" data-testid="app-root">
      <Topbar onHelp={() => setShowHelp(true)} onLogs={() => navigate('/logs')} />
      <div className="flex flex-1 min-h-0">
        <Sidebar collapsed={sidebar} onToggle={() => setSidebar((v) => !v)} />
        <main className="flex-1 min-w-0 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/bookmarks" element={<Bookmarks />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="/help" element={<Help />} />
            <Route path="/api-docs" element={<ApiDocs />} />
            <Route path="/apps" element={<Apps />} />
            <Route path="/logs" element={<Logs />} />
          </Routes>
        </main>
      </div>
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
    </div>
  );
}
