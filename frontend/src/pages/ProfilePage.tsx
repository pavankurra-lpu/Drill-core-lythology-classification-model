import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import GlassCard from '../components/ui/GlassCard';
import { User, Mail, Shield, Calendar, RefreshCw } from 'lucide-react';
import toast from 'react-hot-toast';

const ProfilePage: React.FC = () => {
  const { user } = useAuth();
  const [fullName, setFullName] = useState(user?.full_name || '');
  const [password, setPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleUpdateProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    // Simple update simulation
    await new Promise(r => setTimeout(r, 800));
    setLoading(false);
    toast.success('Profile settings saved.');
  };

  return (
    <div className="space-y-8 max-w-4xl">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Profile Node</h1>
        <p className="text-slate-400 text-sm mt-1">Manage user attributes, tokens, and active session security configurations.</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
        
        {/* Info Sidebar Card */}
        <div className="md:col-span-1 space-y-6">
          <GlassCard className="p-6 text-center space-y-4">
            <div className="h-20 w-20 rounded-full bg-gradient-to-tr from-indigo-500 to-violet-500 flex items-center justify-center font-bold text-3xl text-white mx-auto shadow-lg">
              {user?.username?.substring(0, 2).toUpperCase() || 'US'}
            </div>
            <div>
              <h3 className="text-md font-bold text-white">{user?.full_name}</h3>
              <p className="text-xs text-slate-400">@{user?.username}</p>
            </div>
            
            <div className="h-px bg-slate-800" />
            
            <div className="space-y-3 text-left text-xs text-slate-400">
              <div className="flex items-center gap-2">
                <Shield className="h-4 w-4 text-indigo-400" />
                <span>Role: <b>{user?.role}</b></span>
              </div>
              <div className="flex items-center gap-2">
                <Mail className="h-4 w-4 text-indigo-400" />
                <span className="truncate">{user?.email}</span>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* Update Profile Form Card */}
        <div className="md:col-span-2 space-y-6">
          <GlassCard className="p-6 md:p-8">
            <h3 className="text-md font-bold text-white mb-6">User Profile Configurations</h3>
            
            <form onSubmit={handleUpdateProfile} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Full Name
                </label>
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="glass-input w-full px-4 py-2.5 rounded-xl text-xs"
                  required
                />
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                  Change Password (optional)
                </label>
                <input
                  type="password"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  className="glass-input w-full px-4 py-2.5 rounded-xl text-xs mb-3"
                  placeholder="New Password"
                />
              </div>

              <button
                type="submit"
                disabled={loading}
                className="py-3 px-6 rounded-xl font-semibold text-xs text-white bg-gradient-primary hover:opacity-95 transition-all cursor-pointer disabled:opacity-50 flex items-center gap-2"
              >
                {loading && <RefreshCw className="h-4 w-4 animate-spin" />}
                <span>Save configurations</span>
              </button>
            </form>
          </GlassCard>
        </div>

      </div>
    </div>
  );
};

export default ProfilePage;
