import apiClient from './client'

export const modelsApi = {
  getModelsList: async (): Promise<any[]> => {
    const { data } = await apiClient.get('/api/v1/models/list')
    return data
  },

  getModelInfo: async (modelName: string): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/models/${modelName}/info`)
    return data
  },

  getModelMetrics: async (modelName: string): Promise<any> => {
    const { data } = await apiClient.get(`/api/v1/models/${modelName}/metrics`)
    return data
  },

  compareModels: async (payload: { image_path: string; model_names: string[] }): Promise<any> => {
    const { data } = await apiClient.post('/api/v1/models/compare', payload)
    return data
  },
}

export default modelsApi
