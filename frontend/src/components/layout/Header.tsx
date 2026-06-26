import React from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../hooks/useAuth';
import { Bell, LogOut, Settings, User as UserIcon } from 'lucide-react';
import toast from 'react-hot-toast';

const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout, user } = useAuth();

  // Convert route path to readable Title
  const getPageTitle = () => {
    const path = location.pathname.substring(1);
    if (!path) return 'Dashboard Overview';
    return path.charAt(0).toUpperCase() + path.slice(1).replace('-', ' ');
  };

  const handleLogout = () => {
    logout();
    toast.success('Successfully logged out.');
    navigate('/login');
  };

  return (
    <header className="glass-panel h-16 border-b border-slate-800 flex items-center justify-between px-8 bg-slate-900/10">
      {/* Title */}
      <div>
        <h2 className="text-lg font-bold tracking-tight text-white">{getPageTitle()}</h2>
        <p className="text-[10px] text-slate-400">Automated drill core analysis node</p>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-6">
        {/* Notifications */}
        <button className="text-slate-400 hover:text-slate-200 transition-colors relative">
          <Bell className="h-5 w-5" />
          <span className="absolute -top-1.5 -right-1.5 h-3.5 w-3.5 rounded-full bg-indigo-500 border border-slate-950 flex items-center justify-center text-[8px] font-bold text-white">
            3
          </span>
        </button>

        <div className="h-6 w-px bg-slate-800" />

        {/* Profile Controls */}
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/profile')} 
            className="flex items-center gap-2 text-slate-300 hover:text-white transition-colors"
          >
            <div className="h-8 w-8 rounded-full bg-slate-800 border border-slate-700 flex items-center justify-center text-xs font-semibold text-indigo-400">
              <UserIcon className="h-4 w-4" />
            </div>
            <span className="text-xs font-medium hidden sm:inline">{user?.username}</span>
          </button>
          
          <button 
            onClick={handleLogout} 
            title="Log Out"
            className="text-slate-500 hover:text-red-400 transition-colors ml-2"
          >
            <LogOut className="h-4.5 w-4.5" />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
