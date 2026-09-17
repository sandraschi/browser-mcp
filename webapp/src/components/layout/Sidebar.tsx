import {
  Bookmark,
  ChevronLeft,
  ChevronRight,
  Code2,
  FileText,
  HelpCircle,
  LayoutDashboard,
  LayoutGrid,
  MessageSquare,
  Settings as SettingsIcon,
  Sparkles,
  Terminal,
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

const nav = [
  { to: '/', label: 'Dashboard', icon: LayoutDashboard },
  { to: '/bookmarks', label: 'Bookmarks', icon: Bookmark },
  { to: '/tools', label: 'Tools', icon: Code2 },
  { to: '/chat', label: 'Chat', icon: MessageSquare },
  { to: '/apps', label: 'Apps', icon: LayoutGrid },
  { to: '/skills', label: 'Skills', icon: Sparkles },
  { to: '/settings', label: 'Settings', icon: SettingsIcon },
  { to: '/help', label: 'Help', icon: HelpCircle },
  { to: '/api-docs', label: 'API Docs', icon: FileText },
  { to: '/logs', label: 'Logs', icon: Terminal },
];

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${isActive ? 'bg-amber/20 text-amber' : 'text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200'}`;

export default function Sidebar({ collapsed, onToggle }: SidebarProps) {
  return (
    <aside
      className={`flex flex-col border-r border-zinc-700/50 bg-zinc-950 transition-[width] duration-200 ${collapsed ? 'w-16' : 'w-56'}`}
    >
      <div className="flex items-center gap-2 px-3 pt-4 pb-2 border-b border-zinc-700/50">
        {!collapsed && (
          <div className="flex items-center gap-2 min-w-0 flex-1">
            <span className="text-lg font-bold text-amber shrink-0">▶</span>
            <div className="min-w-0 leading-tight">
              <p className="text-sm font-semibold text-zinc-100 truncate">Browser MCP</p>
              <p className="text-[11px] text-zinc-400">v0.3.0</p>
            </div>
          </div>
        )}
        <button
          type="button"
          onClick={onToggle}
          className="p-1 rounded text-zinc-500 hover:text-zinc-200 hover:bg-zinc-800 shrink-0"
          title={collapsed ? 'Expand' : 'Collapse'}
          data-testid="sidebar-toggle"
        >
          {collapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
        </button>
      </div>
      <nav className="flex-1 py-2 px-2 space-y-0.5">
        {nav.map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} end={to === '/'} className={linkClass} title={collapsed ? label : undefined}>
            <Icon size={18} className="shrink-0" />
            {!collapsed && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
    </aside>
  );
}
