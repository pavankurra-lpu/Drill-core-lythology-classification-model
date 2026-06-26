import { forwardRef } from 'react'
import { clsx } from 'clsx'
import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'success' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
  isLoading?: boolean
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  fullWidth?: boolean
}

const variantClasses: Record<string, string> = {
  primary:
    'bg-gradient-to-r from-primary-500 to-secondary-500 text-white border-transparent shadow-primary-glow hover:opacity-90 hover:shadow-lg',
  secondary:
    'bg-white/10 text-textPrimary border border-white/20 hover:bg-white/15 hover:border-white/30',
  ghost:
    'bg-transparent text-textPrimary border-transparent hover:bg-white/8',
  danger:
    'bg-gradient-to-r from-error to-rose-600 text-white border-transparent hover:opacity-90',
  success:
    'bg-gradient-to-r from-success to-emerald-400 text-white border-transparent hover:opacity-90',
  outline:
    'bg-transparent text-primary-400 border border-primary-500/50 hover:bg-primary-500/10 hover:border-primary-500',
}

const sizeClasses: Record<string, string> = {
  xs: 'px-2.5 py-1 text-xs rounded-lg gap-1',
  sm: 'px-3 py-1.5 text-sm rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-xl gap-2',
  lg: 'px-6 py-3 text-base rounded-xl gap-2',
  xl: 'px-8 py-4 text-lg rounded-2xl gap-3',
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      children,
      variant = 'primary',
      size = 'md',
      isLoading = false,
      leftIcon,
      rightIcon,
      fullWidth = false,
      className,
      disabled,
      ...props
    },
    ref
  ) => {
    return (
      <motion.button
        ref={ref}
        className={clsx(
          'inline-flex items-center justify-center font-medium transition-all duration-200',
          'border focus:outline-none focus:ring-2 focus:ring-primary-500/50 focus:ring-offset-2 focus:ring-offset-transparent',
          'disabled:opacity-50 disabled:cursor-not-allowed',
          variantClasses[variant],
          sizeClasses[size],
          fullWidth && 'w-full',
          className
        )}
        disabled={disabled || isLoading}
        whileHover={!disabled && !isLoading ? { scale: 1.02 } : undefined}
        whileTap={!disabled && !isLoading ? { scale: 0.98 } : undefined}
        {...(props as React.ComponentProps<typeof motion.button>)}
      >
        {isLoading ? (
          <Loader2 className="animate-spin" size={size === 'xs' ? 12 : size === 'sm' ? 14 : 16} />
        ) : (
          leftIcon
        )}
        {children}
        {!isLoading && rightIcon}
      </motion.button>
    )
  }
)

Button.displayName = 'Button'
