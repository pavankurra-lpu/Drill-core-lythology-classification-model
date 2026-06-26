import apiClient from './client'
import type { Dataset, DatasetSample, PaginatedResponse } from '@/types'

export const datasetsApi = {
  uploadDataset: async (
    file: File,
    name: string,
    description?: string,
    onUploadProgress?: (progress: number) => void
  ): Promise<Dataset> => {
    const formData = new FormData()
    formData.append('file', file)
    formData.append('name', name)
    if (description) formData.append('description', description)

    const { data } = await apiClient.post('/api/datasets/upload', formData, {
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

  listDatasets: async (params: {
    page?: number
    per_page?: number
    search?: string
  } = {}): Promise<PaginatedResponse<Dataset>> => {
    const { data } = await apiClient.get('/api/datasets', { params })
    return data
  },

  getDataset: async (id: string): Promise<Dataset> => {
    const { data } = await apiClient.get(`/api/datasets/${id}`)
    return data
  },

  getDatasetSamples: async (
    id: string,
    params: { page?: number; per_page?: number; class_name?: string } = {}
  ): Promise<PaginatedResponse<DatasetSample>> => {
    const { data } = await apiClient.get(`/api/datasets/${id}/samples`, { params })
    return data
  },

  deleteDataset: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/datasets/${id}`)
  },

  getDatasetStats: async (id: string): Promise<Dataset> => {
    const { data } = await apiClient.get(`/api/datasets/${id}/stats`)
    return data
  },
}

export default datasetsApi

