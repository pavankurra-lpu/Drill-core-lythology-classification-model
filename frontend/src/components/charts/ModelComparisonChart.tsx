import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { GlassCard } from '@/components/ui/GlassCard'
import { Skeleton } from '@/components/ui/LoadingSpinner'
import type { ModelPerformance } from '@/types'

interface ModelComparisonChartProps {
  data?: ModelPerformance[]
  isLoading?: boolean
  title?: string
  height?: number
}

const MOCK_DATA: ModelPerformance[] = [
  {
    model_name: 'efficientnet_b3',
    accuracy: 0.947,
    precision: 0.932,
    recall: 0.921,
    f1_score: 0.926,
    avg_inference_time_ms: 145,
    total_predictions: 3421,
  },
  {
    model_name: 'resnet50',
    accuracy: 0.923,
    precision: 0.908,
    recall: 0.899,
    f1_score: 0.903,
    avg_inference_time_ms: 98,
    total_predictions: 2876,
  },
]

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/10 backdrop-blur-glass border border-white/20 rounded-xl p-3 shadow-glass">
        {payload.map((entry, i) => (
          <p key={i} className="text-xs font-medium" style={{ color: entry.color }}>
            {entry.name}: {(entry.value * 100).toFixed(1)}%
          </p>
        ))}
      </div>
    )
  }
  return null
}

export const ModelComparisonChart: React.FC<ModelComparisonChartProps> = ({
  data,
  isLoading = false,
  title = 'Model Performance Comparison',
  height = 320,
}) => {
  const models = data && data.length > 0 ? data : MOCK_DATA

  const radarData = [
    { metric: 'Accuracy', ...Object.fromEntries(models.map(m => [m.model_name, m.accuracy])) },
    { metric: 'Precision', ...Object.fromEntries(models.map(m => [m.model_name, m.precision])) },
    { metric: 'Recall', ...Object.fromEntries(models.map(m => [m.model_name, m.recall])) },
    { metric: 'F1 Score', ...Object.fromEntries(models.map(m => [m.model_name, m.f1_score])) },
  ]

  const colors = ['#6366f1', '#06b6d4']
  const modelDisplayNames: Record<string, string> = {
    efficientnet_b3: 'EfficientNet-B3',
    resnet50: 'ResNet50',
  }

  if (isLoading) {
    return (
      <GlassCard className="p-6">
        <Skeleton className="h-5 w-48 mb-6" />
        <Skeleton className="w-full" style={{ height }} />
      </GlassCard>
    )
  }

  return (
    <GlassCard className="p-6">
      <h3 className="text-base font-semibold text-textPrimary mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <RadarChart data={radarData}>
          <PolarGrid stroke="rgba(255,255,255,0.1)" />
          <PolarAngleAxis
            dataKey="metric"
            tick={{ fill: '#94a3b8', fontSize: 12 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0.7, 1]}
            tick={{ fill: '#64748b', fontSize: 10 }}
            tickCount={4}
          />
          {models.map((model, index) => (
            <Radar
              key={model.model_name}
              name={modelDisplayNames[model.model_name] || model.model_name}
              dataKey={model.model_name}
              stroke={colors[index]}
              fill={colors[index]}
              fillOpacity={0.15}
              strokeWidth={2}
            />
          ))}
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#94a3b8', paddingTop: '8px' }}
          />
        </RadarChart>
      </ResponsiveContainer>
    </GlassCard>
  )
}

export default ModelComparisonChart

