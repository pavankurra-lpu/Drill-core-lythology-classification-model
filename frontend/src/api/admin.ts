import apiClient from './client'
import type { User, SystemHealth, ActivityLog, PaginatedResponse } from '@/types'

export const adminApi = {
  // Users
  listUsers: async (params: {
    page?: number
    per_page?: number
    search?: string
    role?: string
  } = {}): Promise<PaginatedResponse<User>> => {
    const { data } = await apiClient.get('/api/admin/users', { params })
    return data
  },

  getUser: async (id: number): Promise<User> => {
    const { data } = await apiClient.get(`/api/admin/users/${id}`)
    return data
  },

  updateUser: async (id: number, updates: Partial<User>): Promise<User> => {
    const { data } = await apiClient.patch(`/api/admin/users/${id}`, updates)
    return data
  },

  deleteUser: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/admin/users/${id}`)
  },

  toggleUserActive: async (id: number): Promise<User> => {
    const { data } = await apiClient.post(`/api/admin/users/${id}/toggle-active`)
    return data
  },

  // System
  getSystemHealth: async (): Promise<SystemHealth> => {
    const { data } = await apiClient.get('/api/admin/system/health')
    return data
  },

  getActivityLogs: async (params: {
    page?: number
    per_page?: number
    user_id?: number
  } = {}): Promise<PaginatedResponse<ActivityLog>> => {
    const { data } = await apiClient.get('/api/admin/activity-logs', { params })
    return data
  },

  clearCache: async (): Promise<void> => {
    await apiClient.post('/api/admin/system/clear-cache')
  },

  getSystemStats: async (): Promise<{
    total_users: number
    active_users_today: number
    total_predictions: number
    storage_used_gb: number
  }> => {
    const { data } = await apiClient.get('/api/admin/system/stats')
    return data
  },
}

export default adminApi

