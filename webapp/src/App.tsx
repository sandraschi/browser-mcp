import { useState } from 'react';
import { Route, Routes } from 'react-router-dom';
import Topbar from './components/layout/Topbar';
import Sidebar from './components/layout/Sidebar';
import HelpModal from './components/layout/HelpModal';
import LoggerModal from './components/layout/LoggerModal';
import { useZoom } from './hooks/useZoom';
import Dashboard from './pages/Dashboard';
import Bookmarks from './pages/Bookmarks';
import Tools from './pages/Tools';
import Chat from './pages/Chat';
import Skills from './pages/Skills';
import ApiDocs from './pages/ApiDocs';
import Apps from './pages/Apps';

export default function App() {
  useZoom();
  const [sidebar, setSidebar] = useState(false);
  const [showHelp, setShowHelp] = useState(false);
  const [showLogs, setShowLogs] = useState(false);

  return (
    <div className="h-screen flex flex-col bg-zinc-950" data-testid="dashboard">
      <Topbar onHelp={() => setShowHelp(true)} onLogs={() => setShowLogs(true)} />
      <div className="flex flex-1 min-h-0">
        <Sidebar collapsed={sidebar} onToggle={() => setSidebar(v => !v)} />
        <main className="flex-1 min-w-0 p-6 overflow-auto">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/bookmarks" element={<Bookmarks />} />
            <Route path="/tools" element={<Tools />} />
            <Route path="/chat" element={<Chat />} />
            <Route path="/skills" element={<Skills />} />
            <Route path="/api-docs" element={<ApiDocs />} />
            <Route path="/apps" element={<Apps />} />
          </Routes>
        </main>
      </div>
      {showHelp && <HelpModal onClose={() => setShowHelp(false)} />}
      {showLogs && <LoggerModal onClose={() => setShowLogs(false)} />}
    </div>
  );
}
