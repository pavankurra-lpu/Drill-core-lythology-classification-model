import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { format, parseISO } from 'date-fns'
import { GlassCard } from '@/components/ui/GlassCard'
import { Skeleton } from '@/components/ui/LoadingSpinner'
import type { PredictionTimelinePoint } from '@/types'

interface PredictionTimelineChartProps {
  data?: PredictionTimelinePoint[]
  isLoading?: boolean
  title?: string
  height?: number
}

const CustomTooltip = ({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; color: string }>
  label?: string
}) => {
  if (active && payload && payload.length) {
    return (
      <div className="bg-white/10 backdrop-blur-glass border border-white/20 rounded-xl p-3 shadow-glass">
        <p className="text-xs text-textSecondary mb-2">
          {label ? format(parseISO(label), 'MMM d, yyyy') : ''}
        </p>
        {payload.map((entry, index) => (
          <p key={index} className="text-xs font-medium" style={{ color: entry.color }}>
            {entry.name}: {entry.name.includes('Confidence') ? `${(entry.value * 100).toFixed(1)}%` : entry.value}
          </p>
        ))}
      </div>
    )
  }
  return null
}

// Generate 30 days of mock data
const generateMockData = (): PredictionTimelinePoint[] => {
  const data: PredictionTimelinePoint[] = []
  const now = new Date()
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    data.push({
      date: date.toISOString().split('T')[0],
      count: Math.floor(Math.random() * 30) + 5,
      avg_confidence: 0.7 + Math.random() * 0.25,
    })
  }
  return data
}

const MOCK_DATA = generateMockData()

export const PredictionTimelineChart: React.FC<PredictionTimelineChartProps> = ({
  data,
  isLoading = false,
  title = 'Prediction Activity (Last 30 Days)',
  height = 280,
}) => {
  const chartData = data && data.length > 0 ? data : MOCK_DATA

  if (isLoading) {
    return (
      <GlassCard className="p-6">
        <Skeleton className="h-5 w-56 mb-6" />
        <Skeleton className="w-full" style={{ height }} />
      </GlassCard>
    )
  }

  return (
    <GlassCard className="p-6">
      <h3 className="text-base font-semibold text-textPrimary mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <AreaChart data={chartData} margin={{ top: 5, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="gradCount" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#6366f1" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#6366f1" stopOpacity={0} />
            </linearGradient>
            <linearGradient id="gradConfidence" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#06b6d4" stopOpacity={0} />
            </linearGradient>
          </defs>
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" />
          <XAxis
            dataKey="date"
            tickFormatter={(val) => {
              try { return format(parseISO(val), 'MMM d') } catch { return val }
            }}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
            interval="preserveStartEnd"
          />
          <YAxis
            yAxisId="count"
            orientation="left"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <YAxis
            yAxisId="confidence"
            orientation="right"
            domain={[0, 1]}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip content={<CustomTooltip />} />
          <Legend
            wrapperStyle={{ fontSize: '12px', color: '#94a3b8', paddingTop: '8px' }}
          />
          <Area
            yAxisId="count"
            type="monotone"
            dataKey="count"
            name="Predictions"
            stroke="#6366f1"
            strokeWidth={2}
            fill="url(#gradCount)"
            dot={false}
            activeDot={{ r: 4, fill: '#6366f1' }}
          />
          <Area
            yAxisId="confidence"
            type="monotone"
            dataKey="avg_confidence"
            name="Avg Confidence"
            stroke="#06b6d4"
            strokeWidth={2}
            fill="url(#gradConfidence)"
            dot={false}
            activeDot={{ r: 4, fill: '#06b6d4' }}
          />
        </AreaChart>
      </ResponsiveContainer>
    </GlassCard>
  )
}

export default PredictionTimelineChart

