import React from 'react'
import { motion } from 'framer-motion'
import { clsx } from 'clsx'
import { TrendingUp, TrendingDown, Minus } from 'lucide-react'
import { GlassCard } from './GlassCard'
import { Skeleton } from './LoadingSpinner'

interface StatCardProps {
  title: string
  value: string | number
  icon: React.ReactNode
  change?: number // percentage change
  changeLabel?: string
  color?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'accent'
  isLoading?: boolean
  className?: string
  index?: number
}

const colorMap = {
  primary: {
    icon: 'bg-primary-500/20 text-primary-400',
    glow: 'shadow-primary-glow',
    gradient: 'from-primary-500/10 to-transparent',
  },
  secondary: {
    icon: 'bg-purple-500/20 text-purple-400',
    glow: '',
    gradient: 'from-purple-500/10 to-transparent',
  },
  success: {
    icon: 'bg-emerald-500/20 text-emerald-400',
    glow: 'shadow-success-glow',
    gradient: 'from-emerald-500/10 to-transparent',
  },
  warning: {
    icon: 'bg-amber-500/20 text-amber-400',
    glow: '',
    gradient: 'from-amber-500/10 to-transparent',
  },
  error: {
    icon: 'bg-red-500/20 text-red-400',
    glow: '',
    gradient: 'from-red-500/10 to-transparent',
  },
  accent: {
    icon: 'bg-cyan-500/20 text-cyan-400',
    glow: 'shadow-accent-glow',
    gradient: 'from-cyan-500/10 to-transparent',
  },
}

export const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  change,
  changeLabel,
  color = 'primary',
  isLoading = false,
  className,
  index = 0,
}) => {
  const colors = colorMap[color]

  const TrendIcon =
    change === undefined || change === 0
      ? Minus
      : change > 0
      ? TrendingUp
      : TrendingDown

  const trendColor =
    change === undefined || change === 0
      ? 'text-textSecondary'
      : change > 0
      ? 'text-emerald-400'
      : 'text-red-400'

  if (isLoading) {
    return (
      <GlassCard className={clsx('p-6', className)}>
        <div className="flex items-start justify-between">
          <div className="space-y-3 flex-1">
            <Skeleton className="h-4 w-24" />
            <Skeleton className="h-8 w-16" />
            <Skeleton className="h-3 w-32" />
          </div>
          <Skeleton className="w-12 h-12 rounded-xl" />
        </div>
      </GlassCard>
    )
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.1 }}
    >
      <GlassCard
        className={clsx('p-6 relative overflow-hidden', className)}
        hover
      >
        {/* Background gradient */}
        <div
          className={clsx(
            'absolute inset-0 bg-gradient-to-br opacity-50 rounded-2xl',
            colors.gradient
          )}
        />

        <div className="relative flex items-start justify-between">
          <div className="space-y-2">
            <p className="text-sm text-textSecondary font-medium">{title}</p>
            <motion.p
              className="text-3xl font-bold text-textPrimary"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: index * 0.1 + 0.2 }}
            >
              {value}
            </motion.p>
            {change !== undefined && (
              <div className={clsx('flex items-center gap-1 text-xs', trendColor)}>
                <TrendIcon size={12} />
                <span className="font-medium">
                  {Math.abs(change).toFixed(1)}%
                </span>
                {changeLabel && (
                  <span className="text-textSecondary">{changeLabel}</span>
                )}
              </div>
            )}
          </div>

          <motion.div
            className={clsx('p-3 rounded-xl', colors.icon)}
            whileHover={{ scale: 1.1, rotate: 5 }}
            transition={{ type: 'spring', stiffness: 300 }}
          >
            {typeof icon === 'function' ? React.createElement(icon, { size: 20 }) : icon}
          </motion.div>
        </div>
      </GlassCard>
    </motion.div>
  )
}

export default StatCard

