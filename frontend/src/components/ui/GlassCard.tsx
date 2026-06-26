import { forwardRef } from 'react'
import { clsx } from 'clsx'
import { motion } from 'framer-motion'

interface GlassCardProps {
  children: React.ReactNode
  className?: string
  variant?: 'default' | 'elevated' | 'bordered' | 'dark' | 'gradient'
  hover?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  animate?: boolean
  onClick?: () => void
}

const paddingMap = {
  none: '',
  sm: 'p-4',
  md: 'p-6',
  lg: 'p-8',
}

const variantMap = {
  default: 'bg-white/5 border border-white/10 backdrop-blur-glass',
  elevated: 'bg-white/8 border border-white/15 backdrop-blur-glass shadow-glass-lg',
  bordered: 'bg-white/5 border-2 border-primary-500/40 backdrop-blur-glass',
  dark: 'bg-black/30 border border-white/8 backdrop-blur-glass',
  gradient: 'bg-gradient-to-br from-white/10 to-white/5 border border-white/10 backdrop-blur-glass',
}

export const GlassCard = forwardRef<HTMLDivElement, GlassCardProps>(
  (
    {
      children,
      className,
      variant = 'default',
      hover = false,
      padding = 'md',
      animate = false,
      onClick,
    },
    ref
  ) => {
    const baseClasses = clsx(
      'rounded-2xl',
      variantMap[variant],
      paddingMap[padding],
      hover && 'transition-all duration-300 hover:bg-white/10 hover:border-white/20 hover:shadow-glass',
      onClick && 'cursor-pointer',
      className
    )

    if (animate) {
      return (
        <motion.div
          ref={ref}
          className={baseClasses}
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, ease: 'easeOut' }}
          onClick={onClick}
          whileHover={hover ? { scale: 1.01 } : undefined}
          whileTap={onClick ? { scale: 0.99 } : undefined}
        >
          {children}
        </motion.div>
      )
    }

    return (
      <div ref={ref} className={baseClasses} onClick={onClick}>
        {children}
      </div>
    )
  }
)

GlassCard.displayName = 'GlassCard'

export default GlassCard

