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
  getOverview: async (params: AnalyticsParams = {}): Promise<any> => {
    const { data } = await apiClient.get('/api/v1/analytics/overview', { params })
    return data
  },

  getPredictionTimeline: async (
    params: AnalyticsParams = {}
  ): Promise<any[]> => {
    const { data } = await apiClient.get('/api/v1/analytics/predictions/timeline', { params })
    return data
  },

  getLithologyDistribution: async (
    params: AnalyticsParams = {}
  ): Promise<any[]> => {
    const { data } = await apiClient.get('/api/v1/analytics/lithology/distribution', { params })
    return data
  },

  getModelPerformance: async (): Promise<any[]> => {
    const { data } = await apiClient.get('/api/v1/analytics/models/comparison')
    return data
  },

  getTopUsers: async (params: { limit?: number } = {}): Promise<any[]> => {
    const { data } = await apiClient.get('/api/v1/analytics/users/activity', { params })
    return data
  },

  exportAnalytics: async (params: AnalyticsParams = {}): Promise<Blob> => {
    const { data } = await apiClient.get('/api/v1/analytics/export', {
      params,
      responseType: 'blob',
    })
    return data
  },
}

export default analyticsApi
