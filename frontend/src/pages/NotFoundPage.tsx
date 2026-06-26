import React from 'react';
import { useNavigate } from 'react-router-dom';
import GlassCard from '../components/ui/GlassCard';
import { AlertCircle, Home } from 'lucide-react';

const NotFoundPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="h-screen w-screen flex items-center justify-center bg-[#0a0f1e] p-6">
      <GlassCard className="p-8 md:p-10 max-w-md text-center space-y-6 border border-slate-800 shadow-2xl">
        <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20 text-red-400 w-fit mx-auto">
          <AlertCircle className="h-8 w-8 animate-bounce" />
        </div>
        
        <div>
          <h1 className="text-3xl font-extrabold text-white">404 - Lost Horizon</h1>
          <p className="text-xs text-slate-400 mt-2 leading-relaxed">
            The geological stratigraphy index you requested does not exist or has been shifted in geological time.
          </p>
        </div>

        <button
          onClick={() => navigate('/')}
          className="w-full py-3 rounded-xl font-semibold text-xs text-white bg-gradient-primary hover:opacity-95 active:scale-[0.98] transition-all duration-150 flex items-center justify-center gap-2 cursor-pointer shadow-lg"
        >
          <Home className="h-4 w-4" />
          <span>Return to base overview</span>
        </button>
      </GlassCard>
    </div>
  );
};

export default NotFoundPage;
