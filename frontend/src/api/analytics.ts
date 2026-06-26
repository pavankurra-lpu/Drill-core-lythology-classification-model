import apiClient from './client'
import type {
  AnalyticsOverview,
  PredictionTimelinePoint,
  LithologyDistribution,
  ModelPerformance,
  TopUser,
} from '@/types'

export interface AnalyticsParams {
  date_from?: string
  date_to?: string
  granularity?: 'day' | 'week' | 'month'
  model?: string
}

export const analyticsApi = {
  getOverview: async (params: AnalyticsParams = {}): Promise<AnalyticsOverview> => {
    const { data } = await apiClient.get('/api/analytics/overview', { params })
    return data
  },

  getPredictionTimeline: async (
    params: AnalyticsParams = {}
  ): Promise<PredictionTimelinePoint[]> => {
    const { data } = await apiClient.get('/api/analytics/timeline', { params })
    return data
  },

  getLithologyDistribution: async (
    params: AnalyticsParams = {}
  ): Promise<LithologyDistribution[]> => {
    const { data } = await apiClient.get('/api/analytics/distribution', { params })
    return data
  },

  getModelPerformance: async (): Promise<ModelPerformance[]> => {
    const { data } = await apiClient.get('/api/analytics/models/performance')
    return data
  },

  getTopUsers: async (params: { limit?: number } = {}): Promise<TopUser[]> => {
    const { data } = await apiClient.get('/api/analytics/top-users', { params })
    return data
  },

  exportAnalytics: async (params: AnalyticsParams = {}): Promise<Blob> => {
    const { data } = await apiClient.get('/api/analytics/export', {
      params,
      responseType: 'blob',
    })
    return data
  },
}
