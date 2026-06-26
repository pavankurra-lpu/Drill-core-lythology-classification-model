import React from 'react';
import { useQuery } from '@tanstack/react-query';
import modelsApi from '../api/models';
import GlassCard from '../components/ui/GlassCard';
import ModelComparisonChart from '../components/charts/ModelComparisonChart';
import { Cpu, AlertTriangle, ShieldCheck, BarChart2 } from 'lucide-react';

const ModelsPage: React.FC = () => {
  const { data: modelsData, isLoading } = useQuery({
    queryKey: ['models-comparison'],
    queryFn: () => modelsApi.getModelsList()
  });

  const models = modelsData || [];

  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Model Comparison Lab</h1>
        <p className="text-slate-400 text-sm mt-1">Review diagnostic accuracies, latency speeds, and parameters across neural networks.</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Side: Detail Cards */}
        <div className="lg:col-span-2 space-y-6">
          {isLoading ? (
            <div className="text-center text-slate-400 py-12">Loading model weights info...</div>
          ) : models.length === 0 ? (
            <div className="text-center text-slate-500 py-12">No model metrics loaded.</div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {models.map((model: any) => (
                <GlassCard key={model.name} className="p-6 space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="p-3 bg-indigo-500/10 rounded-xl border border-indigo-500/20 text-indigo-400">
                      <Cpu className="h-6 w-6" />
                    </div>
                    <div>
                      <h3 className="text-md font-bold text-white">{model.name}</h3>
                      <span className="text-[10px] text-indigo-400 uppercase font-bold tracking-widest">Active Model Weight</span>
                    </div>
                  </div>

                  <div className="h-px bg-slate-800" />

                  {/* Metrics grid */}
                  <div className="grid grid-cols-2 gap-6 text-xs">
                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Parameters</span>
                      <span className="text-white font-semibold">{model.parameters || 'N/A'}</span>
                    </div>
                    
                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Target Accuracy</span>
                      <span className="text-emerald-400 font-bold text-sm">{(model.accuracy ?? 0).toFixed(1)}%</span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Model Size</span>
                      <span className="text-white font-semibold">{model.size_mb ? `${model.size_mb} MB` : 'N/A'}</span>
                    </div>

                    <div>
                      <span className="text-[10px] text-slate-500 font-bold uppercase tracking-wider block">Input Standard</span>
                      <span className="text-white font-semibold">224 x 224 x 3</span>
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-900/40 border border-slate-800/80 flex items-start gap-2.5">
                    <ShieldCheck className="h-4.5 w-4.5 text-indigo-400 mt-0.5" />
                    <p className="text-[10px] text-slate-400 leading-normal">
                      Verified for mineral classification and rock segmentation under the general drill core index.
                    </p>
                  </div>
                </GlassCard>
              ))}
            </div>
          )}

          {/* Model info banner */}
          <GlassCard className="p-4 bg-yellow-500/5 border-yellow-500/10 flex items-start gap-3">
            <AlertTriangle className="h-5 w-5 text-amber-500 mt-0.5" />
            <div>
              <h5 className="text-xs font-bold text-white">Active Retraining Notice</h5>
              <p className="text-[10px] text-slate-400 leading-relaxed mt-0.5">
                Model training should only be performed on GPU-enabled nodes. Processing training epochs on standard CPU containers might yield significant operational latencies.
              </p>
            </div>
          </GlassCard>
        </div>

        {/* Right Side: Radar Chart Comparison */}
        <GlassCard className="p-6 flex flex-col justify-between h-full">
          <div>
            <h3 className="text-md font-bold text-white mb-2">Architectural Comparison</h3>
            <p className="text-xs text-slate-400 leading-relaxed">
              Visualizing the tradeoffs between F1 score, precision, recall, latency speed, and parameters count.
            </p>
          </div>
          <div className="h-64 mt-6">
            <ModelComparisonChart />
          </div>
        </GlassCard>

      </div>
    </div>
  );
};

export default ModelsPage;
