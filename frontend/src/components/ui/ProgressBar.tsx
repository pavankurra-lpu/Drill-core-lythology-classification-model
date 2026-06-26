import { motion } from 'framer-motion'
import { clsx } from 'clsx'

interface ProgressBarProps {
  value: number // 0 to 1
  label?: string
  showPercentage?: boolean
  color?: string
  size?: 'xs' | 'sm' | 'md' | 'lg'
  animated?: boolean
  striped?: boolean
  className?: string
}

const sizeMap = {
  xs: 'h-1',
  sm: 'h-1.5',
  md: 'h-2.5',
  lg: 'h-4',
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  showPercentage = false,
  color,
  size = 'md',
  animated = true,
  striped = false,
  className,
}) => {
  const clampedValue = Math.min(1, Math.max(0, value))
  const percentage = clampedValue * 100

  const getBarColor = () => {
    if (color) return color
    if (clampedValue >= 0.9) return '#10b981'
    if (clampedValue >= 0.75) return '#06b6d4'
    if (clampedValue >= 0.6) return '#6366f1'
    if (clampedValue >= 0.4) return '#f59e0b'
    return '#ef4444'
  }

  const barColor = getBarColor()

  return (
    <div className={clsx('w-full', className)}>
      {(label || showPercentage) && (
        <div className="flex justify-between items-center mb-2">
          {label && <span className="text-xs text-textSecondary">{label}</span>}
          {showPercentage && (
            <span className="text-xs font-medium" style={{ color: barColor }}>
              {percentage.toFixed(1)}%
            </span>
          )}
        </div>
      )}
      <div className={clsx('w-full bg-white/10 rounded-full overflow-hidden', sizeMap[size])}>
        <motion.div
          className={clsx('h-full rounded-full', striped && 'bg-stripes')}
          style={{
            background: `linear-gradient(90deg, ${barColor}cc, ${barColor})`,
            boxShadow: `0 0 8px ${barColor}60`,
          }}
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: animated ? 0.8 : 0, ease: 'easeOut' }}
        />
      </div>
    </div>
  )
}

// Circular progress variant
interface CircularProgressProps {
  value: number // 0 to 1
  size?: number
  strokeWidth?: number
  color?: string
  label?: React.ReactNode
  className?: string
}

export const CircularProgress: React.FC<CircularProgressProps> = ({
  value,
  size = 80,
  strokeWidth = 6,
  color,
  label,
  className,
}) => {
  const clampedValue = Math.min(1, Math.max(0, value))
  const radius = (size - strokeWidth) / 2
  const circumference = radius * 2 * Math.PI

  const getColor = () => {
    if (color) return color
    if (clampedValue >= 0.9) return '#10b981'
    if (clampedValue >= 0.75) return '#06b6d4'
    if (clampedValue >= 0.6) return '#6366f1'
    if (clampedValue >= 0.4) return '#f59e0b'
    return '#ef4444'
  }

  const barColor = getColor()

  return (
    <div className={clsx('relative inline-flex items-center justify-center', className)}>
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="rgba(255,255,255,0.1)"
          strokeWidth={strokeWidth}
        />
        <motion.circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={barColor}
          strokeWidth={strokeWidth}
          strokeLinecap="round"
          strokeDasharray={circumference}
          initial={{ strokeDashoffset: circumference }}
          animate={{ strokeDashoffset: circumference * (1 - clampedValue) }}
          transition={{ duration: 1, ease: 'easeOut' }}
          style={{ filter: `drop-shadow(0 0 6px ${barColor}80)` }}
        />
      </svg>
      {label && (
        <div className="absolute inset-0 flex items-center justify-center">
          {label}
        </div>
      )}
    </div>
  )
}

export default ProgressBar

