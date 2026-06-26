import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Layers, Mail, Lock, User, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();
  
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [fullName, setFullName] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !username || !fullName || !password || !confirmPassword) {
      toast.error('All fields are required.');
      return;
    }
    if (password !== confirmPassword) {
      toast.error('Passwords do not match.');
      return;
    }
    
    setLoading(true);
    try {
      await register({ email, username, full_name: fullName, password });
      toast.success('Registration successful! Please login.');
      navigate('/login');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Registration failed.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-screen bg-[#0a0f1e] overflow-hidden">
      {/* Left Column - Graphic/Info Panel */}
      <div className="hidden lg:flex w-1/2 flex-col justify-between p-12 bg-gradient-to-br from-indigo-950/60 via-slate-900 to-indigo-950/60 border-r border-slate-800/40 relative">
        <div className="flex items-center gap-3">
          <Layers className="h-9 w-9 text-indigo-500" />
          <h2 className="text-xl font-bold tracking-wider text-white">LITHOS.AI</h2>
        </div>

        <div className="space-y-6 max-w-lg">
          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
            Open API access
          </span>
          <h1 className="text-4xl font-extrabold text-white leading-tight">
            Register your Geological Node
          </h1>
          <p className="text-slate-400 leading-relaxed">
            Gain immediate access to classification pipelines, geological report compilers, and live AI assistant chat capabilities.
          </p>
        </div>

        <p className="text-xs text-slate-500">
          &copy; {new Date().getFullYear()} Lithos AI Corp. All rights reserved.
        </p>
      </div>

      {/* Right Column - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8 overflow-y-auto">
        <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-2xl border border-slate-800 shadow-2xl relative my-8">
          
          <div className="mb-6">
            <h2 className="text-2xl font-bold text-white mb-1">Create Account</h2>
            <p className="text-sm text-slate-400">Get access to classification pipelines</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Full Name
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-2.5 rounded-xl text-sm"
                  placeholder="John Doe"
                  required
                />
                <User className="absolute left-4 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Username
              </label>
              <div className="relative">
                <input
                  type="text"
                  value={username}
                  onChange={(e) => setUsername(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-2.5 rounded-xl text-sm"
                  placeholder="johndoe"
                  required
                />
                <User className="absolute left-4 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-2.5 rounded-xl text-sm"
                  placeholder="name@company.com"
                  required
                />
                <Mail className="absolute left-4 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-2.5 rounded-xl text-sm"
                  placeholder="••••••••"
                  required
                />
                <Lock className="absolute left-4 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-1">
                Confirm Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-2.5 rounded-xl text-sm"
                  placeholder="••••••••"
                  required
                />
                <Lock className="absolute left-4 top-3.5 h-4 w-4 text-slate-500" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl font-semibold text-sm text-white bg-gradient-primary hover:opacity-95 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 shadow-[0_4px_20px_-2px_rgba(99,102,241,0.5)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed mt-2"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4.5 w-4.5 animate-spin" />
                  <span>Registering node...</span>
                </>
              ) : (
                <span>Register Node</span>
              )}
            </button>
          </form>

          <p className="text-center text-xs text-slate-400 mt-6">
            Already have a node?{' '}
            <Link to="/login" className="text-indigo-400 hover:underline font-semibold">
              Sign In
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default RegisterPage;
