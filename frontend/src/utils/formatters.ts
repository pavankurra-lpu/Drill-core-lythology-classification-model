import { format, formatDistanceToNow, parseISO, isValid } from 'date-fns'

// ─── Date Formatters ──────────────────────────────────────────────────────────

export const formatDate = (dateString: string, fmt = 'MMM d, yyyy'): string => {
  try {
    const date = parseISO(dateString)
    if (!isValid(date)) return 'Invalid date'
    return format(date, fmt)
  } catch {
    return 'Invalid date'
  }
}

export const formatDateTime = (dateString: string): string => {
  return formatDate(dateString, 'MMM d, yyyy HH:mm')
}

export const formatRelativeTime = (dateString: string): string => {
  try {
    const date = parseISO(dateString)
    if (!isValid(date)) return 'Unknown'
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown'
  }
}

export const formatShortDate = (dateString: string): string => {
  return formatDate(dateString, 'MM/dd/yy')
}

// ─── Number Formatters ────────────────────────────────────────────────────────

export const formatConfidence = (confidence: number): string => {
  return `${(confidence * 100).toFixed(1)}%`
}

export const formatPercentage = (value: number): string => {
  return `${value.toFixed(1)}%`
}

export const formatNumber = (value: number): string => {
  if (value >= 1_000_000) return `${(value / 1_000_000).toFixed(1)}M`
  if (value >= 1_000) return `${(value / 1_000).toFixed(1)}K`
  return value.toString()
}

export const formatFileSize = (bytes: number): string => {
  if (bytes < 1024) return `${bytes} B`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
  if (bytes < 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`
  return `${(bytes / (1024 * 1024 * 1024)).toFixed(1)} GB`
}

export const formatDuration = (ms: number): string => {
  if (ms < 1000) return `${ms.toFixed(0)}ms`
  return `${(ms / 1000).toFixed(2)}s`
}

// ─── Confidence → Color Mapping ───────────────────────────────────────────────

export const confidenceToColor = (confidence: number): string => {
  if (confidence >= 0.9) return '#10b981' // emerald - very high
  if (confidence >= 0.75) return '#06b6d4' // cyan - high
  if (confidence >= 0.6) return '#6366f1'  // indigo - medium
  if (confidence >= 0.4) return '#f59e0b'  // amber - low
  return '#ef4444'                          // red - very low
}

export const confidenceToLabel = (confidence: number): string => {
  if (confidence >= 0.9) return 'Very High'
  if (confidence >= 0.75) return 'High'
  if (confidence >= 0.6) return 'Moderate'
  if (confidence >= 0.4) return 'Low'
  return 'Very Low'
}

export const confidenceToBadgeClass = (confidence: number): string => {
  if (confidence >= 0.9) return 'badge-success'
  if (confidence >= 0.75) return 'badge-accent'
  if (confidence >= 0.6) return 'badge-primary'
  if (confidence >= 0.4) return 'badge-warning'
  return 'badge-error'
}

// ─── Rock / Lithology Icons ───────────────────────────────────────────────────

export const LITHOLOGY_COLORS: Record<string, string> = {
  granite: '#e87d4d',
  basalt: '#4a4a6a',
  sandstone: '#d4a855',
  limestone: '#8fb8d4',
  shale: '#7a7a8a',
  quartzite: '#e8e8f0',
  gneiss: '#8a6a5a',
  marble: '#f0ece8',
  conglomerate: '#c4a87a',
  dolomite: '#aad4c4',
  andesite: '#7a6a8a',
  rhyolite: '#d4b4a4',
  obsidian: '#1a1a2a',
  chalk: '#f8f8f0',
  mudstone: '#8a8a6a',
  arkose: '#c48a6a',
  default: '#6366f1',
}

export const getLithologyColor = (lithology: string): string => {
  const key = lithology.toLowerCase()
  return LITHOLOGY_COLORS[key] || LITHOLOGY_COLORS.default
}

export const LITHOLOGY_CHART_COLORS = [
  '#6366f1', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b',
  '#ef4444', '#ec4899', '#14b8a6', '#f97316', '#84cc16',
]

export const getLithologyChartColor = (index: number): string => {
  return LITHOLOGY_CHART_COLORS[index % LITHOLOGY_CHART_COLORS.length]
}

// ─── Status Helpers ───────────────────────────────────────────────────────────

export const statusToColor: Record<string, string> = {
  healthy: '#10b981',
  degraded: '#f59e0b',
  down: '#ef4444',
  completed: '#10b981',
  processing: '#06b6d4',
  pending: '#f59e0b',
  failed: '#ef4444',
  ready: '#10b981',
  uploading: '#6366f1',
  error: '#ef4444',
}

export const getStatusColor = (status: string): string => {
  return statusToColor[status.toLowerCase()] || '#94a3b8'
}

// ─── Text Helpers ─────────────────────────────────────────────────────────────

export const truncateText = (text: string, maxLength: number): string => {
  if (text.length <= maxLength) return text
  return `${text.substring(0, maxLength)}...`
}

export const capitalize = (str: string): string => {
  return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase()
}

export const titleCase = (str: string): string => {
  return str
    .split(/[_\s]+/)
    .map(capitalize)
    .join(' ')
}
