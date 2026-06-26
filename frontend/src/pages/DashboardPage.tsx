import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useAnalytics } from '../hooks/useAnalytics';
import StatCard from '../components/ui/StatCard';
import GlassCard from '../components/ui/GlassCard';
import LithologyDistributionChart from '../components/charts/LithologyDistributionChart';
import PredictionTimelineChart from '../components/charts/PredictionTimelineChart';
import { 
  FileText, 
  Layers, 
  Flame, 
  ShieldAlert, 
  ArrowRight,
  UploadCloud,
  MessageSquareCode
} from 'lucide-react';

const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const { data: stats, isLoading } = useAnalytics();

  // Handle loading skeletons
  if (isLoading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-10 w-64 bg-slate-800 rounded" />
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-32 bg-slate-800 rounded-xl" />
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="h-80 lg:col-span-2 bg-slate-800 rounded-xl" />
          <div className="h-80 bg-slate-800 rounded-xl" />
        </div>
      </div>
    );
  }

  // Fallback calculations for visualization safety
  const totalPreds = stats?.total_predictions ?? 0;
  const successRate = stats?.prediction_stats?.success_rate ?? 100;
  const totalDatasets = stats?.total_datasets ?? 0;
  const totalReports = stats?.total_reports ?? 0;

  return (
    <div className="space-y-8">
      {/* Welcome Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl md:text-3xl font-extrabold text-white">Dashboard Overview</h1>
          <p className="text-slate-400 text-sm mt-1">Live analytics, predictions feed, and diagnostic utilities.</p>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={() => navigate('/predict')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-primary hover:opacity-95 text-white font-medium text-xs shadow-lg active:scale-95 transition-all cursor-pointer"
          >
            <UploadCloud className="h-4 w-4" />
            <span>Classify New Core</span>
          </button>
          
          <button 
            onClick={() => navigate('/chat')}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white font-medium text-xs active:scale-95 transition-all cursor-pointer"
          >
            <MessageSquareCode className="h-4 w-4 text-indigo-400" />
            <span>Consult GeoChat</span>
          </button>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
        <StatCard 
          title="Total Predictions" 
          value={totalPreds} 
          trend="+12%" 
          trendDirection="up" 
          icon={Layers} 
        />
        <StatCard 
          title="Success Rate" 
          value={`${successRate.toFixed(1)}%`} 
          trend="+0.4%" 
          trendDirection="up" 
          icon={Flame} 
        />
        <StatCard 
          title="Uploaded Datasets" 
          value={totalDatasets} 
          trend="Flat" 
          trendDirection="neutral" 
          icon={ShieldAlert} 
        />
        <StatCard 
          title="Generated Reports" 
          value={totalReports} 
          trend="+8%" 
          trendDirection="up" 
          icon={FileText} 
        />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Timeline Area Chart */}
        <div className="lg:col-span-2">
          <GlassCard className="p-6 h-full flex flex-col justify-between">
            <div className="mb-4">
              <h3 className="text-md font-bold text-white">Prediction Timeline</h3>
              <p className="text-xs text-slate-400">Drill core logs ingested over the last 30 days.</p>
            </div>
            <div className="h-64 flex-1">
              <PredictionTimelineChart />
            </div>
          </GlassCard>
        </div>

        {/* Lithology Distribution Pie Chart */}
        <div>
          <GlassCard className="p-6 h-full flex flex-col justify-between">
            <div className="mb-4">
              <h3 className="text-md font-bold text-white">Lithology Mix</h3>
              <p className="text-xs text-slate-400">Breakdown of classified rock samples.</p>
            </div>
            <div className="h-64 flex-1 flex items-center justify-center">
              <LithologyDistributionChart />
            </div>
          </GlassCard>
        </div>
      </div>

      {/* Action Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <GlassCard className="p-6 flex flex-col justify-between hover:border-indigo-500/20 transition-all duration-300">
          <div>
            <h4 className="text-md font-bold text-white mb-2">Model Lab comparison</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload sample image to evaluate prediction performance between EfficientNet-B3 and ResNet50 models simultaneously.
            </p>
          </div>
          <button 
            onClick={() => navigate('/models')}
            className="flex items-center gap-1.5 text-xs text-indigo-400 font-semibold mt-4 hover:text-indigo-300 transition-colors"
          >
            <span>Compare model weights</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </GlassCard>

        <GlassCard className="p-6 flex flex-col justify-between hover:border-violet-500/20 transition-all duration-300">
          <div>
            <h4 className="text-md font-bold text-white mb-2">Geological Q&A Assistant</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Upload PDF reports and query our RAG knowledge base. Inquire about minerals, stratigraphic formations, and drill summaries.
            </p>
          </div>
          <button 
            onClick={() => navigate('/chat')}
            className="flex items-center gap-1.5 text-xs text-violet-400 font-semibold mt-4 hover:text-violet-300 transition-colors"
          >
            <span>Open Chat interface</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </GlassCard>

        <GlassCard className="p-6 flex flex-col justify-between hover:border-cyan-500/20 transition-all duration-300">
          <div>
            <h4 className="text-md font-bold text-white mb-2">Custom Retraining Suite</h4>
            <p className="text-xs text-slate-400 leading-relaxed">
              Ingest custom drill datasets (packaged as .zip aggregates), validate labels, and trigger asynchronous retraining jobs.
            </p>
          </div>
          <button 
            onClick={() => navigate('/datasets')}
            className="flex items-center gap-1.5 text-xs text-cyan-400 font-semibold mt-4 hover:text-cyan-300 transition-colors"
          >
            <span>Manage datasets</span>
            <ArrowRight className="h-3.5 w-3.5" />
          </button>
        </GlassCard>
      </div>
    </div>
  );
};

export default DashboardPage;
