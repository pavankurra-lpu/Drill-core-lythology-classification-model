import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Layers, Mail, Lock, Loader2 } from 'lucide-react';
import toast from 'react-hot-toast';

const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const { login } = useAuth();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) {
      toast.error('Please enter all fields.');
      return;
    }
    
    setLoading(true);
    try {
      await login(email, password);
      toast.success('Successfully logged in!');
      navigate('/dashboard');
    } catch (err: any) {
      toast.error(err.response?.data?.detail || 'Invalid email or password.');
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
            Enterprise Grade System
          </span>
          <h1 className="text-4xl font-extrabold text-white leading-tight">
            Automated Drill Core Lithology Classification
          </h1>
          <p className="text-slate-400 leading-relaxed">
            Harnessing Computer Vision (EfficientNet-B3/ResNet50) and LLM-driven RAG analysis to accelerate geological core logging workflows.
          </p>
        </div>

        <p className="text-xs text-slate-500">
          &copy; {new Date().getFullYear()} Lithos AI Corp. All rights reserved.
        </p>
        
        {/* Glow bubbles */}
        <div className="absolute top-1/4 left-1/4 h-80 w-80 bg-indigo-500/10 rounded-full blur-[100px] pointer-events-none" />
        <div className="absolute bottom-1/4 right-1/4 h-80 w-80 bg-violet-500/10 rounded-full blur-[100px] pointer-events-none" />
      </div>

      {/* Right Column - Form */}
      <div className="w-full lg:w-1/2 flex items-center justify-center p-8">
        <div className="glass-panel w-full max-w-md p-8 md:p-10 rounded-2xl border border-slate-800 shadow-2xl relative">
          
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-white mb-2">Welcome Back</h2>
            <p className="text-sm text-slate-400">Sign in to access your geological node</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <div className="relative">
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-3 rounded-xl text-sm"
                  placeholder="name@company.com"
                  required
                />
                <Mail className="absolute left-4 top-3.5 h-4.5 w-4.5 text-slate-500" />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2">
                Password
              </label>
              <div className="relative">
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="glass-input w-full pl-11 pr-4 py-3 rounded-xl text-sm"
                  placeholder="••••••••"
                  required
                />
                <Lock className="absolute left-4 top-3.5 h-4.5 w-4.5 text-slate-500" />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl font-semibold text-sm text-white bg-gradient-primary hover:opacity-95 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 shadow-[0_4px_20px_-2px_rgba(99,102,241,0.5)] cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? (
                <>
                  <Loader2 className="h-4.5 w-4.5 animate-spin" />
                  <span>Authenticating...</span>
                </>
              ) : (
                <span>Sign In</span>
              )}
            </button>
          </form>

          <p className="text-center text-xs text-slate-400 mt-8">
            Don't have an account?{' '}
            <Link to="/register" className="text-indigo-400 hover:underline font-semibold">
              Create free node
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
};

export default LoginPage;
