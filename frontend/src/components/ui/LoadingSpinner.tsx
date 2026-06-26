import { motion } from 'framer-motion'
import { clsx } from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  variant?: 'ring' | 'dots' | 'pulse' | 'geo'
  color?: string
  className?: string
  label?: string
}

const sizeMap = {
  sm: 'w-6 h-6',
  md: 'w-10 h-10',
  lg: 'w-16 h-16',
  xl: 'w-24 h-24',
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  variant = 'ring',
  color = '#6366f1',
  className,
  label,
}) => {
  if (variant === 'dots') {
    return (
      <div className={clsx('flex items-center justify-center gap-2', className)}>
        {[0, 1, 2].map((i) => (
          <motion.div
            key={i}
            className="w-2.5 h-2.5 rounded-full"
            style={{ backgroundColor: color }}
            animate={{ scale: [1, 1.5, 1], opacity: [0.5, 1, 0.5] }}
            transition={{ duration: 1, delay: i * 0.2, repeat: Infinity }}
          />
        ))}
        {label && <span className="ml-2 text-sm text-textSecondary">{label}</span>}
      </div>
    )
  }

  if (variant === 'pulse') {
    return (
      <div className={clsx('flex flex-col items-center justify-center gap-4', className)}>
        <motion.div
          className={clsx('rounded-full', sizeMap[size])}
          style={{ backgroundColor: color, opacity: 0.3 }}
          animate={{ scale: [1, 1.5, 1], opacity: [0.3, 0.7, 0.3] }}
          transition={{ duration: 1.5, repeat: Infinity }}
        />
        {label && <p className="text-sm text-textSecondary animate-pulse">{label}</p>}
      </div>
    )
  }

  if (variant === 'geo') {
    return (
      <div className={clsx('flex flex-col items-center justify-center gap-4', className)}>
        <div className={clsx('relative', sizeMap[size])}>
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-primary-500/30"
            animate={{ scale: [1, 1.4, 1], opacity: [1, 0, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border-2 border-accent/50"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
          <motion.div
            className="absolute inset-4 rounded-full"
            style={{ backgroundColor: color }}
            animate={{ scale: [0.8, 1, 0.8] }}
            transition={{ duration: 1.5, repeat: Infinity }}
          />
        </div>
        {label && <p className="text-sm text-textSecondary">{label}</p>}
      </div>
    )
  }

  // Default: ring
  return (
    <div className={clsx('flex flex-col items-center justify-center gap-3', className)}>
      <motion.div
        className={clsx('rounded-full border-2 border-transparent', sizeMap[size])}
        style={{
          borderTopColor: color,
          borderRightColor: `${color}60`,
        }}
        animate={{ rotate: 360 }}
        transition={{ duration: 0.8, repeat: Infinity, ease: 'linear' }}
      />
      {label && <p className="text-sm text-textSecondary animate-pulse">{label}</p>}
    </div>
  )
}

// Full page loading overlay
export const PageLoader: React.FC<{ label?: string }> = ({ label = 'Loading...' }) => {
  return (
    <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
      <motion.div
        initial={{ opacity: 0, scale: 0.8 }}
        animate={{ opacity: 1, scale: 1 }}
        className="flex flex-col items-center gap-6"
      >
        <div className="relative w-24 h-24">
          <motion.div
            className="absolute inset-0 rounded-full border-2 border-primary-500/20"
            animate={{ scale: [1, 1.5, 1], opacity: [1, 0, 1] }}
            transition={{ duration: 2, repeat: Infinity }}
          />
          <motion.div
            className="absolute inset-2 rounded-full border-2 border-accent/40"
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: 'linear' }}
          />
          <motion.div
            className="absolute inset-4 rounded-full border-2 border-secondary-500/60"
            animate={{ rotate: -180 }}
            transition={{ duration: 1.5, repeat: Infinity, ease: 'linear' }}
          />
          <div className="absolute inset-6 rounded-full bg-gradient-to-br from-primary-500 to-secondary-500 flex items-center justify-center">
            <span className="text-white text-lg">⬡</span>
          </div>
        </div>
        <div className="text-center">
          <p className="text-textPrimary font-semibold">{label}</p>
          <p className="text-textSecondary text-sm mt-1">GeoVision AI</p>
        </div>
      </motion.div>
    </div>
  )
}

// Skeleton loading block
export const Skeleton: React.FC<{ className?: string }> = ({ className }) => {
  return (
    <div
      className={clsx(
        'bg-white/10 rounded-lg animate-pulse',
        className
      )}
    />
  )
}
