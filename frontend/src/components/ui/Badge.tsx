import React from 'react'
import { clsx } from 'clsx'

interface BadgeProps {
  children?: React.ReactNode
  content?: React.ReactNode
  variant?: 'primary' | 'secondary' | 'success' | 'warning' | 'error' | 'info' | 'neutral' | 'indigo' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  dot?: boolean
  className?: string
}

const variantClasses: Record<string, string> = {
  primary: 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30',
  indigo: 'bg-indigo-500/20 text-indigo-300 border border-indigo-500/30',
  secondary: 'bg-purple-500/20 text-purple-300 border border-purple-500/30',
  success: 'bg-emerald-500/20 text-emerald-300 border border-emerald-500/30',
  warning: 'bg-amber-500/20 text-amber-300 border border-amber-500/30',
  error: 'bg-red-500/20 text-red-300 border border-red-500/30',
  danger: 'bg-red-500/20 text-red-300 border border-red-500/30',
  info: 'bg-cyan-500/20 text-cyan-300 border border-cyan-500/30',
  neutral: 'bg-white/10 text-slate-400 border border-white/20',
}

const dotColors: Record<string, string> = {
  primary: 'bg-indigo-400',
  indigo: 'bg-indigo-400',
  secondary: 'bg-purple-400',
  success: 'bg-emerald-400',
  warning: 'bg-amber-400',
  error: 'bg-red-400',
  danger: 'bg-red-400',
  info: 'bg-cyan-400',
  neutral: 'bg-slate-400',
}

const sizeClasses: Record<string, string> = {
  sm: 'px-2 py-0.5 text-xs rounded-md',
  md: 'px-2.5 py-1 text-xs rounded-lg',
  lg: 'px-3 py-1.5 text-sm rounded-lg',
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  content,
  variant = 'primary',
  size = 'md',
  dot = false,
  className,
}) => {
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 font-medium',
        variantClasses[variant] || variantClasses['primary'],
        sizeClasses[size],
        className
      )}
    >
      {dot && (
        <span
          className={clsx('inline-block w-1.5 h-1.5 rounded-full', dotColors[variant] || dotColors['primary'])}
        />
      )}
      {content || children}
    </span>
  )
}

export default Badge
