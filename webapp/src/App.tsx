import { Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Bookmarks from './pages/Bookmarks';

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `block px-4 py-2 rounded ${isActive ? 'bg-indigo-600 text-white' : 'text-gray-300 hover:bg-gray-700'}`;

export default function App() {
  return (
    <div className="flex h-screen bg-gray-900 text-gray-100">
      <nav className="w-56 bg-gray-800 p-4 border-r border-gray-700">
        <h1 className="text-lg font-bold mb-6 text-indigo-400">Browser MCP</h1>
        <div className="space-y-1">
          <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
          <NavLink to="/bookmarks" className={linkClass}>Bookmarks</NavLink>
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
