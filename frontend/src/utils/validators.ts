// ─── Form Validation Utilities ────────────────────────────────────────────────

export interface ValidationResult {
  isValid: boolean
  error?: string
}

export const validateEmail = (email: string): ValidationResult => {
  if (!email) return { isValid: false, error: 'Email is required' }
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  if (!emailRegex.test(email)) {
    return { isValid: false, error: 'Please enter a valid email address' }
  }
  return { isValid: true }
}

export const validatePassword = (password: string): ValidationResult => {
  if (!password) return { isValid: false, error: 'Password is required' }
  if (password.length < 8) {
    return { isValid: false, error: 'Password must be at least 8 characters long' }
  }
  if (!/[A-Z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one uppercase letter' }
  }
  if (!/[a-z]/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one lowercase letter' }
  }
  if (!/\d/.test(password)) {
    return { isValid: false, error: 'Password must contain at least one number' }
  }
  return { isValid: true }
}

export const validateConfirmPassword = (
  password: string,
  confirmPassword: string
): ValidationResult => {
  if (!confirmPassword) return { isValid: false, error: 'Please confirm your password' }
  if (password !== confirmPassword) {
    return { isValid: false, error: 'Passwords do not match' }
  }
  return { isValid: true }
}

export const validateUsername = (username: string): ValidationResult => {
  if (!username) return { isValid: false, error: 'Username is required' }
  if (username.length < 3) {
    return { isValid: false, error: 'Username must be at least 3 characters' }
  }
  if (username.length > 30) {
    return { isValid: false, error: 'Username cannot exceed 30 characters' }
  }
  const usernameRegex = /^[a-zA-Z0-9_-]+$/
  if (!usernameRegex.test(username)) {
    return { isValid: false, error: 'Username can only contain letters, numbers, hyphens and underscores' }
  }
  return { isValid: true }
}

export const validateFullName = (fullName: string): ValidationResult => {
  if (!fullName) return { isValid: false, error: 'Full name is required' }
  if (fullName.trim().length < 2) {
    return { isValid: false, error: 'Full name must be at least 2 characters' }
  }
  if (fullName.length > 100) {
    return { isValid: false, error: 'Full name cannot exceed 100 characters' }
  }
  return { isValid: true }
}

export const validateImageFile = (file: File): ValidationResult => {
  const validTypes = ['image/jpeg', 'image/jpg', 'image/png', 'image/tiff', 'image/bmp', 'image/webp']
  if (!validTypes.includes(file.type)) {
    return {
      isValid: false,
      error: 'Please upload an image file (JPEG, PNG, TIFF, BMP, or WebP)',
    }
  }
  const maxSizeMB = 20
  if (file.size > maxSizeMB * 1024 * 1024) {
    return {
      isValid: false,
      error: `Image file size must not exceed ${maxSizeMB}MB`,
    }
  }
  return { isValid: true }
}

export const validateDatasetFile = (file: File): ValidationResult => {
  if (file.type !== 'application/zip' && !file.name.endsWith('.zip')) {
    return { isValid: false, error: 'Dataset must be a ZIP file' }
  }
  const maxSizeGB = 2
  if (file.size > maxSizeGB * 1024 * 1024 * 1024) {
    return { isValid: false, error: `Dataset file size must not exceed ${maxSizeGB}GB` }
  }
  return { isValid: true }
}

export const getPasswordStrength = (password: string): {
  score: number
  label: string
  color: string
} => {
  let score = 0
  if (password.length >= 8) score++
  if (password.length >= 12) score++
  if (/[A-Z]/.test(password)) score++
  if (/[a-z]/.test(password)) score++
  if (/\d/.test(password)) score++
  if (/[^A-Za-z0-9]/.test(password)) score++

  if (score <= 2) return { score, label: 'Weak', color: '#ef4444' }
  if (score <= 4) return { score, label: 'Moderate', color: '#f59e0b' }
  if (score <= 5) return { score, label: 'Strong', color: '#06b6d4' }
  return { score, label: 'Very Strong', color: '#10b981' }
}
