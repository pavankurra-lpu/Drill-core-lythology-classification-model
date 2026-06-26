import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { GlassCard } from '@/components/ui/GlassCard'
import { Skeleton } from '@/components/ui/LoadingSpinner'
import { LITHOLOGY_CHART_COLORS, formatPercentage } from '@/utils/formatters'
import type { LithologyDistribution } from '@/types'

interface LithologyDistributionChartProps {
  data?: LithologyDistribution[]
  isLoading?: boolean
  title?: string
  height?: number
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ name: string; value: number; payload: LithologyDistribution }>
}) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload
    return (
      <div className="bg-white/10 backdrop-blur-glass border border-white/20 rounded-xl p-3 shadow-glass">
        <p className="font-semibold text-textPrimary text-sm">{item.lithology}</p>
        <p className="text-xs text-textSecondary">Count: {item.count}</p>
        <p className="text-xs" style={{ color: LITHOLOGY_CHART_COLORS[0] }}>
          Share: {formatPercentage(item.percentage)}
        </p>
        <p className="text-xs text-textSecondary">
          Avg Confidence: {formatPercentage(item.avg_confidence * 100)}
        </p>
      </div>
    )
  }
  return null
}

const CustomLegend = ({
  payload,
}: {
  payload?: Array<{ value: string; color: string }>
}) => {
  if (!payload) return null
  return (
    <ul className="flex flex-wrap gap-2 justify-center mt-2">
      {payload.map((entry, index) => (
        <li key={index} className="flex items-center gap-1.5 text-xs text-textSecondary">
          <span
            className="inline-block w-2 h-2 rounded-full"
            style={{ backgroundColor: entry.color }}
          />
          {entry.value}
        </li>
      ))}
    </ul>
  )
}

// Mock data for when no data is available
const MOCK_DATA: LithologyDistribution[] = [
  { lithology: 'Granite', count: 145, percentage: 29, avg_confidence: 0.92, color: '#6366f1' },
  { lithology: 'Basalt', count: 98, percentage: 19.6, avg_confidence: 0.88, color: '#8b5cf6' },
  { lithology: 'Sandstone', count: 87, percentage: 17.4, avg_confidence: 0.85, color: '#06b6d4' },
  { lithology: 'Limestone', count: 74, percentage: 14.8, avg_confidence: 0.90, color: '#10b981' },
  { lithology: 'Shale', count: 58, percentage: 11.6, avg_confidence: 0.82, color: '#f59e0b' },
  { lithology: 'Quartzite', count: 38, percentage: 7.6, avg_confidence: 0.78, color: '#ef4444' },
]

export const LithologyDistributionChart: React.FC<LithologyDistributionChartProps> = ({
  data,
  isLoading = false,
  title = 'Lithology Distribution',
  height = 320,
}) => {
  const chartData = data && data.length > 0 ? data : MOCK_DATA

  if (isLoading) {
    return (
      <GlassCard className="p-6">
        <Skeleton className="h-5 w-40 mb-6" />
        <Skeleton className={`w-full`} style={{ height }} />
      </GlassCard>
    )
  }

  return (
    <GlassCard className="p-6">
      <h3 className="text-base font-semibold text-textPrimary mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <PieChart>
          <Pie
            data={chartData}
            cx="50%"
            cy="50%"
            innerRadius={60}
            outerRadius={100}
            paddingAngle={3}
            dataKey="count"
            nameKey="lithology"
          >
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={LITHOLOGY_CHART_COLORS[index % LITHOLOGY_CHART_COLORS.length]}
                stroke="rgba(255,255,255,0.1)"
                strokeWidth={1}
              />
            ))}
          </Pie>
          <Tooltip content={<CustomTooltip />} />
          <Legend content={<CustomLegend />} />
        </PieChart>
      </ResponsiveContainer>
    </GlassCard>
  )
}

export default LithologyDistributionChart

