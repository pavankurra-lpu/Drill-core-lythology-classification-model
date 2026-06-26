import apiClient from './client'
import type { User, AuthTokens, LoginCredentials, RegisterData } from '@/types'

export interface LoginResponse {
  user: User
  tokens: AuthTokens
}

export const authApi = {
  login: async (credentials: LoginCredentials): Promise<LoginResponse> => {
    const { data } = await apiClient.post('/api/auth/login', credentials)
    return data
  },

  register: async (registerData: RegisterData): Promise<LoginResponse> => {
    const { data } = await apiClient.post('/api/auth/register', registerData)
    return data
  },

  logout: async (): Promise<void> => {
    await apiClient.post('/api/auth/logout')
  },

  me: async (): Promise<User> => {
    const { data } = await apiClient.get('/api/auth/me')
    return data
  },

  refreshToken: async (refreshToken: string): Promise<AuthTokens> => {
    const { data } = await apiClient.post('/api/auth/refresh', {
      refresh_token: refreshToken,
    })
    return data
  },

  updateProfile: async (updates: Partial<User>): Promise<User> => {
    const { data } = await apiClient.patch('/api/auth/me', updates)
    return data
  },

  changePassword: async (payload: {
    current_password: string
    new_password: string
  }): Promise<void> => {
    await apiClient.post('/api/auth/change-password', payload)
  },

  uploadAvatar: async (file: File): Promise<{ avatar_url: string }> => {
    const formData = new FormData()
    formData.append('avatar', file)
    const { data } = await apiClient.post('/api/auth/avatar', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
    return data
  },
}
