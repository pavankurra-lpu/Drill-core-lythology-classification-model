import React from 'react';
import GlassCard from '../components/ui/GlassCard';
import LithologyDistributionChart from '../components/charts/LithologyDistributionChart';
import PredictionTimelineChart from '../components/charts/PredictionTimelineChart';
import ConfidenceChart from '../components/charts/ConfidenceChart';
import { BarChart3, LineChart, PieChart } from 'lucide-react';

const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-8">
      {/* Title */}
      <div>
        <h1 className="text-2xl md:text-3xl font-extrabold text-white">Analytics Panel</h1>
        <p className="text-slate-400 text-sm mt-1">Deep-dive visual analysis of core sample metrics and geological predictions.</p>
      </div>

      {/* Grid Layout for Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        {/* Prediction Timeline */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <LineChart className="h-5 w-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Daily Core Scan Ingestion</h3>
          </div>
          <div className="h-64">
            <PredictionTimelineChart />
          </div>
        </GlassCard>

        {/* Lithology distribution */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-2 mb-4">
            <PieChart className="h-5 w-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Class Distribution Mix</h3>
          </div>
          <div className="h-64 flex items-center justify-center">
            <LithologyDistributionChart />
          </div>
        </GlassCard>

        {/* Confidence Scores Chart */}
        <GlassCard className="p-6 lg:col-span-2">
          <div className="flex items-center gap-2 mb-4">
            <BarChart3 className="h-5 w-5 text-indigo-400" />
            <h3 className="text-sm font-bold text-white">Predictive Confidence Distribution</h3>
          </div>
          <div className="h-64">
            <ConfidenceChart />
          </div>
        </GlassCard>

      </div>
    </div>
  );
};

export default AnalyticsPage;
