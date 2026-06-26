import apiClient from './client'
import type {
  Prediction,
  PredictionResult,
  PaginatedResponse,
  PredictionFilterParams,
} from '@/types'

export const predictionsApi = {
  uploadAndPredict: async (
    file: File,
    model: string = 'efficientnet_b3',
    topK: number = 5,
    onUploadProgress?: (progress: number) => void
  ): Promise<PredictionResult> => {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('model', model)
    formData.append('top_k', String(topK))

    const { data } = await apiClient.post('/api/predictions/predict', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (progressEvent) => {
        if (onUploadProgress && progressEvent.total) {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          onUploadProgress(progress)
        }
      },
    })
    return data
  },

  getPrediction: async (id: string): Promise<Prediction> => {
    const { data } = await apiClient.get(`/api/predictions/${id}`)
    return data
  },

  listPredictions: async (
    params: PredictionFilterParams = {}
  ): Promise<PaginatedResponse<Prediction>> => {
    const { data } = await apiClient.get('/api/predictions', { params })
    return data
  },

  deletePrediction: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/predictions/${id}`)
  },

  exportPredictions: async (params: PredictionFilterParams = {}): Promise<Blob> => {
    const { data } = await apiClient.get('/api/predictions/export', {
      params,
      responseType: 'blob',
    })
    return data
  },

  getPredictionImage: (id: string): string => {
    return `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/predictions/${id}/image`
  },
}
