// All TypeScript interfaces for the Lithology Classification System

// ─── Authentication ───────────────────────────────────────────────────────────

export interface User {
  id: number
  email: string
  username: string
  full_name: string
  role: 'admin' | 'user' | 'viewer'
  avatar_url?: string
  is_active: boolean
  created_at: string
  last_login?: string
  prediction_count: number
  api_calls_today: number
  api_calls_limit: number
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
}

export interface LoginCredentials {
  email: string
  password: string
  remember_me?: boolean
}

export interface RegisterData {
  full_name: string
  email: string
  username: string
  password: string
  confirm_password: string
}

export interface UpdateProfileData {
  full_name?: string
  username?: string
  avatar_url?: string
}

export interface ChangePasswordData {
  current_password: string
  new_password: string
  confirm_password: string
}

// ─── Predictions ──────────────────────────────────────────────────────────────

export interface TopKPrediction {
  rank: number
  class_name: string
  class_label: string
  confidence: number
  description?: string
}

export interface MineralPrediction {
  mineral_name: string
  confidence: number
  color: string
}

export interface PredictionResult {
  prediction_id: string
  rock_type: string
  lithology_class: string
  confidence: number
  top_k_predictions: TopKPrediction[]
  mineral_predictions: MineralPrediction[]
  model_used: string
  processing_time_ms: number
  image_url: string
  created_at: string
  notes?: string
  report_id?: string
}

export interface Prediction {
  id: string
  user_id: number
  image_filename: string
  image_url: string
  model_used: string
  status: 'pending' | 'processing' | 'completed' | 'failed'
  result?: PredictionResult
  created_at: string
  updated_at: string
}

export interface PredictRequest {
  model: 'efficientnet_b3' | 'resnet50'
  top_k?: number
  notes?: string
}

// ─── Datasets ─────────────────────────────────────────────────────────────────

export interface DatasetClass {
  class_name: string
  sample_count: number
  percentage: number
}

export interface DatasetSample {
  id: string
  filename: string
  class_name: string
  thumbnail_url: string
  created_at: string
}

export interface Dataset {
  id: string
  name: string
  description?: string
  user_id: number
  status: 'uploading' | 'processing' | 'ready' | 'error'
  total_samples: number
  num_classes: number
  classes: DatasetClass[]
  file_size_mb: number
  created_at: string
  updated_at: string
}

// ─── Reports ──────────────────────────────────────────────────────────────────

export interface Report {
  id: string
  prediction_id: string
  user_id: number
  title: string
  summary: string
  rock_type: string
  lithology_class: string
  confidence: number
  pdf_url?: string
  created_at: string
  prediction?: Prediction
}

export interface GenerateReportRequest {
  prediction_id: string
  title?: string
  include_charts?: boolean
  include_mineral_analysis?: boolean
}

// ─── Chat ─────────────────────────────────────────────────────────────────────

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  created_at: string
  sources?: ChatSource[]
  prediction_context?: string
}

export interface ChatSource {
  title: string
  content: string
  score: number
  source_type: 'document' | 'web' | 'knowledge_base'
}

export interface ChatSession {
  id: string
  user_id: number
  title: string
  mode: 'general' | 'prediction_analysis' | 'report_qa'
  prediction_id?: string
  report_id?: string
  message_count: number
  created_at: string
  updated_at: string
  last_message?: string
}

export interface SendMessageRequest {
  session_id: string
  content: string
  prediction_id?: string
}

// ─── Analytics ────────────────────────────────────────────────────────────────

export interface AnalyticsOverview {
  total_predictions: number
  predictions_today: number
  predictions_this_week: number
  predictions_this_month: number
  avg_confidence: number
  avg_processing_time_ms: number
  total_datasets: number
  total_reports: number
  predictions_change_pct: number
  confidence_change_pct: number
  top_lithology: string
  active_users: number
}

export interface PredictionTimelinePoint {
  date: string
  count: number
  avg_confidence: number
}

export interface LithologyDistribution {
  lithology: string
  count: number
  percentage: number
  avg_confidence: number
  color: string
}

export interface ModelPerformance {
  model_name: string
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  avg_inference_time_ms: number
  total_predictions: number
}

export interface TopUser {
  user_id: number
  username: string
  full_name: string
  prediction_count: number
  last_active: string
}

// ─── Models ───────────────────────────────────────────────────────────────────

export interface ModelMetrics {
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  top_5_accuracy: number
  auc_roc: number
}

export interface ModelInfo {
  id: string
  name: string
  display_name: string
  architecture: string
  parameters_millions: number
  input_size: string
  description: string
  metrics: ModelMetrics
  is_active: boolean
  version: string
  trained_at: string
  training_dataset: string
  num_classes: number
  class_names: string[]
}

export interface ModelComparison {
  model_a: ModelInfo
  model_b: ModelInfo
  winner: string
  comparison_notes: string
}

// ─── Admin ────────────────────────────────────────────────────────────────────

export interface SystemHealth {
  database: 'healthy' | 'degraded' | 'down'
  redis: 'healthy' | 'degraded' | 'down'
  celery: 'healthy' | 'degraded' | 'down'
  storage: 'healthy' | 'degraded' | 'down'
  cpu_usage: number
  memory_usage: number
  disk_usage: number
  uptime_hours: number
}

export interface ActivityLog {
  id: string
  user_id: number
  username: string
  action: string
  details: string
  ip_address: string
  created_at: string
}

// ─── Shared ───────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  per_page: number
  pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiError {
  detail: string
  status_code: number
  errors?: Record<string, string[]>
}

export type SortOrder = 'asc' | 'desc'

export interface FilterParams {
  page?: number
  per_page?: number
  sort_by?: string
  sort_order?: SortOrder
  search?: string
  date_from?: string
  date_to?: string
}

export interface PredictionFilterParams extends FilterParams {
  lithology_class?: string
  model_used?: string
  min_confidence?: number
  max_confidence?: number
  status?: string
}
