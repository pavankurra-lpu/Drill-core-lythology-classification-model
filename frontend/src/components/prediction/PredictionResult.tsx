import React from 'react';
import { useNavigate } from 'react-router-dom';
import GlassCard from '../ui/GlassCard';
import ProgressBar from '../ui/ProgressBar';
import Badge from '../ui/Badge';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Cell } from 'recharts';
import { FileText, MessageSquareCode, Settings } from 'lucide-react';
import { useMutation, useQueryClient } from '@tanstack/react-query';
import reportsApi from '../../api/reports';
import toast from 'react-hot-toast';

interface TopK {
  class: string;
  confidence: number;
}

interface PredictionResultData {
  id: number;
  rock_type: string;
  lithology_class: string;
  confidence_score: number;
  mineral_predictions: Record<string, number>;
  top_predictions: TopK[];
  processing_time: number;
  image_path: string;
}

interface PredictionResultProps {
  data: PredictionResultData;
}

const PredictionResult: React.FC<PredictionResultProps> = ({ data }) => {
  const navigate = useNavigate();
  const queryClient = useQueryClient();

  const generateReportMutation = useMutation({
    mutationFn: () => reportsApi.generateReport({ prediction_id: data.id, title: `Report for Core Sample #${data.id}` }),
    onSuccess: (res) => {
      toast.success('Report successfully compiled!');
      queryClient.invalidateQueries({ queryKey: ['reports'] });
      navigate('/reports');
    },
    onError: () => {
      toast.error('Failed to generate geological report.');
    }
  });

  // Prepare top predictions chart data
  const chartData = data.top_predictions?.map(item => ({
    name: item.class,
    confidence: parseFloat(item.confidence.toFixed(1))
  })) || [];

  const COLORS = ['#6366f1', '#8b5cf6', '#a78bfa', '#c084fc', '#e879f9'];

  return (
    <div className="space-y-6">
      {/* Overview Card */}
      <GlassCard className="p-6 md:p-8 flex flex-col md:flex-row items-center gap-8">
        
        {/* Core Sample Image */}
        <div className="w-full md:w-1/3 flex flex-col items-center">
          <div className="relative rounded-2xl overflow-hidden border border-slate-700 bg-slate-900/60 aspect-square w-full flex items-center justify-center">
            {data.image_path ? (
              <img 
                src={`http://localhost:8000${data.image_path}`} 
                alt="Drill core sample analyzed" 
                className="object-cover w-full h-full"
              />
            ) : (
              <span className="text-xs text-slate-500">Core Image unavailable</span>
            )}
          </div>
          <div className="mt-3 flex items-center gap-2 text-slate-500 text-[10px] uppercase font-bold tracking-wider">
            <Settings className="h-3 w-3" />
            <span>Latency: {data.processing_time.toFixed(2)} seconds</span>
          </div>
        </div>

        {/* Diagnosis Results */}
        <div className="flex-1 space-y-5 w-full">
          <div>
            <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold tracking-widest bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">
              Diagnostic Node Output
            </span>
            <h2 className="text-3xl font-extrabold text-white mt-2">{data.lithology_class}</h2>
            <div className="flex flex-wrap items-center gap-3 mt-2">
              <Badge content={`Rock Type: ${data.rock_type}`} variant="indigo" />
              <Badge 
                content={`Confidence: ${data.confidence_score.toFixed(1)}%`} 
                variant={data.confidence_score >= 80 ? 'success' : data.confidence_score >= 50 ? 'warning' : 'danger'} 
              />
            </div>
          </div>

          <div className="h-px bg-slate-800" />

          {/* Quick Stats */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Quantification Matrix</p>
              <h4 className="text-lg font-bold text-white mt-1">
                {Object.keys(data.mineral_predictions || {}).length} Minerals Detected
              </h4>
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-slate-500 tracking-wider">Analysis Model</p>
              <h4 className="text-lg font-bold text-white mt-1">EfficientNet-B3</h4>
            </div>
          </div>

          <div className="flex flex-wrap gap-3 pt-2">
            <button
              onClick={() => generateReportMutation.mutate()}
              disabled={generateReportMutation.isPending}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-primary hover:opacity-95 text-white font-medium text-xs shadow-lg cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <FileText className="h-4 w-4" />
              <span>{generateReportMutation.isPending ? 'Generating Report...' : 'Compile PDF Report'}</span>
            </button>
            <button
              onClick={() => navigate('/chat', { state: { prediction: data } })}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-slate-800 border border-slate-700 hover:bg-slate-700 text-white font-medium text-xs cursor-pointer"
            >
              <MessageSquareCode className="h-4 w-4 text-indigo-400" />
              <span>Consult Chat Assistant</span>
            </button>
          </div>
        </div>
      </GlassCard>

      {/* Detail Breakdown Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Top Class Confidences Chart */}
        <GlassCard className="p-6 flex flex-col justify-between">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white">Top Classifier Confidences</h3>
            <p className="text-xs text-slate-400">Relative probabilistic scores from model head output.</p>
          </div>
          <div className="h-56 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} layout="vertical" margin={{ left: 10, right: 30 }}>
                <XAxis type="number" stroke="#475569" fontSize={10} domain={[0, 100]} />
                <YAxis dataKey="name" type="category" stroke="#475569" fontSize={10} width={80} />
                <Bar dataKey="confidence" fill="#6366f1" radius={[0, 4, 4, 0]} barSize={16}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </GlassCard>

        {/* Mineral Quantification List */}
        <GlassCard className="p-6">
          <div className="mb-4">
            <h3 className="text-sm font-bold text-white">Mineralogical Quantification</h3>
            <p className="text-xs text-slate-400">Estimated relative abundance percentages.</p>
          </div>
          <div className="space-y-4 max-h-56 overflow-y-auto pr-2">
            {Object.entries(data.mineral_predictions || {}).map(([minName, val]) => {
              const pct = val * 100;
              return (
                <div key={minName} className="space-y-1.5">
                  <div className="flex justify-between text-xs">
                    <span className="font-semibold text-slate-300">{minName}</span>
                    <span className="text-indigo-400 font-bold">{pct.toFixed(1)}%</span>
                  </div>
                  <ProgressBar progress={pct} variant="indigo" size="sm" animated />
                </div>
              );
            })}
            {!data.mineral_predictions && (
              <p className="text-xs text-slate-500">No mineral predictions available.</p>
            )}
          </div>
        </GlassCard>

      </div>
    </div>
  );
};

export default PredictionResult;
