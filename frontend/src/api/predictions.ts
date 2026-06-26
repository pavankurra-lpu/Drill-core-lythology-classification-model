import apiClient from './client'
import type {
  Prediction,
  PredictionResult,
  PaginatedResponse,
  PredictionFilterParams,
} from '@/types'

export const predictionsApi = {
  uploadImage: async (
    file: File,
    modelUsed: string = 'EfficientNet-B3'
  ): Promise<any> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('model_used', modelUsed)

    const { data } = await apiClient.post('/api/v1/predictions/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    return data
  },

  getPrediction: async (id: number): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/predictions/${id}`)
    return data
  },

  listPredictions: async (
    page: number = 1,
    perPage: number = 20
  ): Promise<any> => {
    const { data } = await apiClient.get('/api/v1/predictions/', {
      params: { page, per_page: perPage }
    })
    return data
  },

  deletePrediction: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/v1/predictions/${id}`)
  },

  exportPredictions: async (params: PredictionFilterParams = {}): Promise<Blob> => {
    const { data } = await apiClient.get('/api/v1/predictions/export', {
      params,
      responseType: 'blob',
    })
    return data
  },

  getPredictionImage: (id: string): string => {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/predictions/${id}/image`
  },
}

export default predictionsApi
