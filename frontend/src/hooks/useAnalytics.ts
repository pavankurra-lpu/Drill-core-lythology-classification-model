import { useQuery } from '@tanstack/react-query'
import { analyticsApi, type AnalyticsParams } from '@/api/analytics'

export const useAnalyticsOverview = (params: AnalyticsParams = {}) => {
  return useQuery({
    queryKey: ['analytics', 'overview', params],
    queryFn: () => analyticsApi.getOverview(params),
    staleTime: 5 * 60 * 1000, // 5 min
  })
}

export const useAnalytics = useAnalyticsOverview


export const usePredictionTimeline = (params: AnalyticsParams = {}) => {
  return useQuery({
    queryKey: ['analytics', 'timeline', params],
    queryFn: () => analyticsApi.getPredictionTimeline(params),
    staleTime: 5 * 60 * 1000,
  })
}

export const useLithologyDistribution = (params: AnalyticsParams = {}) => {
  return useQuery({
    queryKey: ['analytics', 'distribution', params],
    queryFn: () => analyticsApi.getLithologyDistribution(params),
    staleTime: 5 * 60 * 1000,
  })
}

export const useModelPerformance = () => {
  return useQuery({
    queryKey: ['analytics', 'model-performance'],
    queryFn: analyticsApi.getModelPerformance,
    staleTime: 10 * 60 * 1000, // 10 min
  })
}

export const useTopUsers = (limit: number = 10) => {
  return useQuery({
    queryKey: ['analytics', 'top-users', limit],
    queryFn: () => analyticsApi.getTopUsers({ limit }),
    staleTime: 5 * 60 * 1000,
  })
}
