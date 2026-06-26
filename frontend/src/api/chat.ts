import apiClient from './client'
import type { ChatSession, ChatMessage, SendMessageRequest, PaginatedResponse } from '@/types'

export const chatApi = {
  createSession: async (payload: {
    title?: string
    mode?: string
    prediction_id?: string
    report_id?: string
  }): Promise<ChatSession> => {
    const { data } = await apiClient.post('/api/chat/sessions', payload)
    return data
  },

  listSessions: async (params: {
    page?: number
    per_page?: number
  } = {}): Promise<PaginatedResponse<ChatSession>> => {
    const { data } = await apiClient.get('/api/chat/sessions', { params })
    return data
  },

  getSession: async (id: string): Promise<ChatSession> => {
    const { data } = await apiClient.get(`/api/chat/sessions/${id}`)
    return data
  },

  deleteSession: async (id: string): Promise<void> => {
    await apiClient.delete(`/api/chat/sessions/${id}`)
  },

  getMessages: async (
    sessionId: string,
    params: { page?: number; per_page?: number } = {}
  ): Promise<PaginatedResponse<ChatMessage>> => {
    const { data } = await apiClient.get(`/api/chat/sessions/${sessionId}/messages`, { params })
    return data
  },

  sendMessage: async (request: SendMessageRequest): Promise<ChatMessage> => {
    const { data } = await apiClient.post(
      `/api/chat/sessions/${request.session_id}/messages`,
      {
        content: request.content,
        prediction_id: request.prediction_id,
      }
    )
    return data
  },

  uploadDocument: async (
    sessionId: string,
    file: File
  ): Promise<{ document_id: string; filename: string }> => {
    const formData = new FormData()
    formData.append('document', file)
    const { data } = await apiClient.post(
      `/api/chat/sessions/${sessionId}/documents`,
      formData,
      { headers: { 'Content-Type': 'multipart/form-data' } }
    )
    return data
  },

  semanticSearch: async (
    sessionId: string,
    query: string
  ): Promise<{ results: Array<{ content: string; score: number; title: string }> }> => {
    const { data } = await apiClient.post(`/api/chat/sessions/${sessionId}/search`, { query })
    return data
  },
}

export default chatApi

