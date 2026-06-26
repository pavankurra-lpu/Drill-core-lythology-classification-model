import { useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { useAuthStore } from '@/store/authStore'
import { authApi } from '@/api/auth'
import type { LoginCredentials, RegisterData } from '@/types'

export const useAuth = () => {
  const navigate = useNavigate()
  const { user, tokens, isAuthenticated, login, logout: logoutStore, updateUser, setLoading, isLoading } = useAuthStore()

  const loginMutation = useMutation({
    mutationFn: authApi.login,
    onSuccess: (data) => {
      login(data.user, data.tokens)
      toast.success(`Welcome back, ${data.user.full_name}!`)
      navigate('/dashboard')
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Login failed. Please check your credentials.'
      toast.error(message)
    },
  })

  const registerMutation = useMutation({
    mutationFn: authApi.register,
    onSuccess: (data) => {
      login(data.user, data.tokens)
      toast.success('Account created successfully! Welcome to GeoVision AI.')
      navigate('/dashboard')
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      const message = error.response?.data?.detail || 'Registration failed. Please try again.'
      toast.error(message)
    },
  })

  const logoutMutation = useMutation({
    mutationFn: authApi.logout,
    onSettled: () => {
      logoutStore()
      navigate('/login')
      toast.success('Logged out successfully')
    },
  })

  const handleLogin = useCallback(
    (credentials: LoginCredentials) => {
      loginMutation.mutate(credentials)
    },
    [loginMutation]
  )

  const handleRegister = useCallback(
    (data: RegisterData) => {
      registerMutation.mutate(data)
    },
    [registerMutation]
  )

  const handleLogout = useCallback(() => {
    logoutMutation.mutate()
  }, [logoutMutation])

  const isAdmin = user?.role === 'admin'
  const isUser = user?.role === 'user' || user?.role === 'admin'

  return {
    user,
    tokens,
    isAuthenticated,
    isLoading: isLoading || loginMutation.isPending || registerMutation.isPending,
    isAdmin,
    isUser,
    login: handleLogin,
    register: handleRegister,
    logout: handleLogout,
    updateUser,
    setLoading,
    loginError: loginMutation.error,
    registerError: registerMutation.error,
  }
}
