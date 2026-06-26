import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { 
  LayoutDashboard, 
  Upload, 
  History, 
  FileText, 
  MessageSquare, 
  Database, 
  Cpu, 
  BarChart3, 
  User, 
  ShieldAlert,
  Layers
} from 'lucide-react';

const Sidebar: React.FC = () => {
  const { user } = useAuth();

  const navItems = [
    { to: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
    { to: '/predict', label: 'Core Classifier', icon: Upload },
    { to: '/history', label: 'History log', icon: History },
    { to: '/reports', label: 'Reports', icon: FileText },
    { to: '/chat', label: 'GeoChat AI', icon: MessageSquare },
    { to: '/datasets', label: 'Dataset Mgr', icon: Database },
    { to: '/models', label: 'Model Lab', icon: Cpu },
    { to: '/analytics', label: 'Analytics', icon: BarChart3 },
    { to: '/profile', label: 'Profile', icon: User },
  ];

  return (
    <aside className="glass-panel w-64 flex flex-col h-full border-r border-slate-800">
      {/* Brand Logo */}
      <div className="flex items-center gap-3 p-6 border-b border-slate-800">
        <Layers className="h-8 w-8 text-indigo-500 animate-pulse" />
        <div>
          <h1 className="text-md font-bold tracking-wider text-white">LITHOS.AI</h1>
          <span className="text-[10px] uppercase text-indigo-400 font-semibold tracking-widest">Core Classifier</span>
        </div>
      </div>

      {/* Nav Menu */}
      <nav className="flex-1 px-4 py-6 space-y-1.5 overflow-y-auto">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-indigo-600/30 to-violet-600/30 text-white border-l-4 border-indigo-500 shadow-[0_0_15px_-3px_rgba(99,102,241,0.4)]'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`
              }
            >
              <Icon className="h-5 w-5" />
              <span>{item.label}</span>
            </NavLink>
          );
        })}

        {/* Admin Section */}
        {user?.role === 'admin' && (
          <>
            <div className="pt-6 pb-2 px-4">
              <span className="text-[10px] uppercase tracking-wider text-slate-500 font-bold">Admin Portal</span>
            </div>
            <NavLink
              to="/admin"
              className={({ isActive }) =>
                `flex items-center gap-3.5 px-4 py-3 rounded-xl text-sm font-medium transition-all duration-200 ${
                  isActive
                    ? 'bg-gradient-to-r from-red-600/30 to-rose-600/30 text-white border-l-4 border-red-500 shadow-[0_0_15px_-3px_rgba(239,68,68,0.4)]'
                    : 'text-slate-400 hover:bg-slate-800/40 hover:text-slate-200'
                }`
              }
            >
              <ShieldAlert className="h-5 w-5" />
              <span>Admin Console</span>
            </NavLink>
          </>
        )}
      </nav>

      {/* User Info footer */}
      <div className="p-4 border-t border-slate-800 bg-slate-900/20">
        <div className="flex items-center gap-3">
          <div className="h-9 w-9 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-sm text-white">
            {user?.username?.substring(0, 2).toUpperCase() || 'US'}
          </div>
          <div className="flex-1 overflow-hidden">
            <h4 className="text-xs font-semibold text-white truncate">{user?.username}</h4>
            <p className="text-[10px] text-slate-500 truncate">{user?.email}</p>
          </div>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
