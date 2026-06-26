import React from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Cell,
  ResponsiveContainer,
} from 'recharts'
import { GlassCard } from '@/components/ui/GlassCard'
import { LITHOLOGY_CHART_COLORS, formatPercentage } from '@/utils/formatters'
import type { TopKPrediction } from '@/types'

interface ConfidenceChartProps {
  data?: TopKPrediction[]
  title?: string
  height?: number
}

const CustomTooltip = ({
  active,
  payload,
}: {
  active?: boolean
  payload?: Array<{ value: number; payload: TopKPrediction }>
}) => {
  if (active && payload && payload.length) {
    const item = payload[0].payload
    return (
      <div className="bg-white/10 backdrop-blur-glass border border-white/20 rounded-xl p-3 shadow-glass">
        <p className="font-semibold text-textPrimary text-sm">#{item.rank} {item.class_label}</p>
        <p className="text-xs text-textSecondary">{item.class_name}</p>
        <p className="text-xs text-indigo-400 font-medium mt-1">
          Confidence: {formatPercentage(item.confidence * 100)}
        </p>
      </div>
    )
  }
  return null
}

const MOCK_DATA: TopKPrediction[] = [
  { rank: 1, class_label: 'Sandstone', class_name: 'Sandstone', confidence: 0.85, description: '' },
  { rank: 2, class_label: 'Limestone', class_name: 'Limestone', confidence: 0.10, description: '' },
  { rank: 3, class_label: 'Shale', class_name: 'Shale', confidence: 0.03, description: '' },
  { rank: 4, class_label: 'Granite', class_name: 'Granite', confidence: 0.01, description: '' },
  { rank: 5, class_label: 'Basalt', class_name: 'Basalt', confidence: 0.01, description: '' },
]

export const ConfidenceChart: React.FC<ConfidenceChartProps> = ({
  data,
  title = 'Predictive Confidence Mix',
  height = 220,
}) => {
  const chartData = data && data.length > 0 ? data : MOCK_DATA

  return (
    <GlassCard className="p-6">
      <h3 className="text-base font-semibold text-textPrimary mb-4">{title}</h3>
      <ResponsiveContainer width="100%" height={height}>
        <BarChart
          data={chartData}
          layout="vertical"
          margin={{ top: 0, right: 30, left: 0, bottom: 0 }}
        >
          <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.06)" horizontal={false} />
          <XAxis
            type="number"
            domain={[0, 1]}
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={{ stroke: 'rgba(255,255,255,0.1)' }}
            tickLine={false}
          />
          <YAxis
            type="category"
            dataKey="class_label"
            tick={{ fill: '#94a3b8', fontSize: 11 }}
            axisLine={false}
            tickLine={false}
            width={80}
          />
          <Tooltip content={<CustomTooltip />} cursor={{ fill: 'rgba(255,255,255,0.04)' }} />
          <Bar dataKey="confidence" radius={[0, 4, 4, 0]} maxBarSize={20}>
            {chartData.map((_, index) => (
              <Cell
                key={`cell-${index}`}
                fill={LITHOLOGY_CHART_COLORS[index % LITHOLOGY_CHART_COLORS.length]}
                style={{ filter: `drop-shadow(0 0 4px ${LITHOLOGY_CHART_COLORS[index % LITHOLOGY_CHART_COLORS.length]}60)` }}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </GlassCard>
  )
}

export default ConfidenceChart
