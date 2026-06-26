import apiClient from './client'
import type { Report, GenerateReportRequest, PaginatedResponse } from '@/types'

export const reportsApi = {
  generateReport: async (request: GenerateReportRequest): Promise<Report> => {
    const { data } = await apiClient.post('/api/reports/generate', request)
    return data
  },

  listReports: async (params: {
    page?: number
    per_page?: number
    search?: string
  } = {}): Promise<PaginatedResponse<Report>> => {
    const { data } = await apiClient.get('/api/reports', { params })
    return data
  },

  getReport: async (id: string): Promise<Report> => {
    const { data } = await apiClient.get(`/api/reports/${id}`)
    return data
  },

  downloadReportPdf: async (id: string): Promise<Blob> => {
    const { data } = await apiClient.get(`/api/reports/${id}/pdf`, {
      responseType: 'blob',
    })
    return data
  },

  deleteReport: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/reports/${id}`)
  },

  getReportPreviewUrl: (id: string): string => {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/reports/${id}/preview`
  },
}

export default reportsApi

