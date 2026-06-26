import { forwardRef, useState } from 'react'
import { clsx } from 'clsx'
import { Eye, EyeOff } from 'lucide-react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  hint?: string
  leftIcon?: React.ReactNode
  rightIcon?: React.ReactNode
  variant?: 'default' | 'filled'
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  (
    {
      label,
      error,
      hint,
      leftIcon,
      rightIcon,
      variant = 'default',
      type,
      className,
      id,
      ...props
    },
    ref
  ) => {
    const [showPassword, setShowPassword] = useState(false)
    const isPassword = type === 'password'
    const inputType = isPassword ? (showPassword ? 'text' : 'password') : type
    const inputId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={inputId}
            className="block text-sm font-medium text-textSecondary mb-2"
          >
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-textSecondary">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={inputId}
            type={inputType}
            className={clsx(
              'w-full text-sm rounded-xl transition-all duration-200 outline-none',
              'placeholder:text-textSecondary/50',
              variant === 'default'
                ? 'bg-white/5 border border-white/10 hover:border-white/20 focus:border-primary-500/60 focus:bg-white/8 focus:ring-2 focus:ring-primary-500/20'
                : 'bg-white/8 border border-transparent focus:border-primary-500/60 focus:ring-2 focus:ring-primary-500/20',
              'text-textPrimary py-3',
              leftIcon ? 'pl-10' : 'pl-4',
              isPassword || rightIcon ? 'pr-12' : 'pr-4',
              error && 'border-error/60 focus:border-error/80 focus:ring-error/20',
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary hover:text-textPrimary transition-colors"
            >
              {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
            </button>
          )}
          {!isPassword && rightIcon && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-textSecondary">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <p className="text-xs text-error mt-1.5 flex items-center gap-1">
            <span className="inline-block w-1 h-1 rounded-full bg-error" />
            {error}
          </p>
        )}
        {hint && !error && (
          <p className="text-xs text-textSecondary mt-1.5">{hint}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

// Textarea variant
interface TextareaProps extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {
  label?: string
  error?: string
  hint?: string
}

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ label, error, hint, className, id, ...props }, ref) => {
    const textareaId = id || label?.toLowerCase().replace(/\s+/g, '-')

    return (
      <div className="w-full">
        {label && (
          <label
            htmlFor={textareaId}
            className="block text-sm font-medium text-textSecondary mb-2"
          >
            {label}
          </label>
        )}
        <textarea
          ref={ref}
          id={textareaId}
          className={clsx(
            'w-full px-4 py-3 text-sm rounded-xl transition-all duration-200 outline-none resize-none',
            'bg-white/5 border border-white/10',
            'text-textPrimary placeholder:text-textSecondary/50',
            'hover:border-white/20 focus:border-primary-500/60 focus:bg-white/8 focus:ring-2 focus:ring-primary-500/20',
            error && 'border-error/60 focus:border-error/80',
            className
          )}
          {...props}
        />
        {error && (
          <p className="text-xs text-error mt-1.5">{error}</p>
        )}
        {hint && !error && (
          <p className="text-xs text-textSecondary mt-1.5">{hint}</p>
        )}
      </div>
    )
  }
)

Textarea.displayName = 'Textarea'
