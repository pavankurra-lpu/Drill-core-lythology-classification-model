import apiClient from './client'
import type { ModelInfo, ModelComparison } from '@/types'

export const modelsApi = {
  listModels: async (): Promise<ModelInfo[]> => {
    const { data } = await apiClient.get('/api/models')
    return data
  },

  getModel: async (id: string): Promise<ModelInfo> => {
    const { data } = await apiClient.get(`/api/models/${id}`)
    return data
  },

  compareModels: async (modelA: string, modelB: string): Promise<ModelComparison> => {
    const { data } = await apiClient.get('/api/models/compare', {
      params: { model_a: modelA, model_b: modelB },
    })
    return data
  },

  predictWithModel: async (
    file: File,
    modelId: string,
    topK: number = 5
  ): Promise<{ model: string; predictions: Array<{ class: string; confidence: number }> }> => {
    const formData = new FormData()
    formData.append('image', file)
    formData.append('top_k', String(topK))
    const { data } = await apiClient.post(`/api/models/${modelId}/predict`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },

  triggerRetraining: async (modelId: string, datasetId: string): Promise<{ task_id: string }> => {
    const { data } = await apiClient.post(`/api/models/${modelId}/retrain`, {
      dataset_id: datasetId,
    })
    return data
  },

  getRetrainingStatus: async (taskId: string): Promise<{
    status: 'pending' | 'running' | 'completed' | 'failed'
    progress: number
    message: string
  }> => {
    const { data } = await apiClient.get(`/api/models/retrain/${taskId}/status`)
    return data
  },
}
