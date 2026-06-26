import { useState, useCallback } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { predictionsApi } from '@/api/predictions'
import type { PredictionResult, PredictionFilterParams } from '@/types'

export const usePrediction = () => {
  const queryClient = useQueryClient()
  const [uploadProgress, setUploadProgress] = useState(0)
  const [currentResult, setCurrentResult] = useState<PredictionResult | null>(null)

  const predictMutation = useMutation({
    mutationFn: ({
      file,
      model,
      topK,
    }: {
      file: File
      model: string
      topK?: number
    }) =>
      predictionsApi.uploadAndPredict(file, model, topK || 5, (progress) => {
        setUploadProgress(progress)
      }),
    onSuccess: (result) => {
      setCurrentResult(result)
      setUploadProgress(0)
      toast.success(`Analysis complete! Detected: ${result.lithology_class}`)
      queryClient.invalidateQueries({ queryKey: ['predictions'] })
    },
    onError: (error: { response?: { data?: { detail?: string } } }) => {
      setUploadProgress(0)
      toast.error(error.response?.data?.detail || 'Prediction failed. Please try again.')
    },
  })

  const predict = useCallback(
    (file: File, model: string, topK?: number) => {
      predictMutation.mutate({ file, model, topK })
    },
    [predictMutation]
  )

  const clearResult = useCallback(() => {
    setCurrentResult(null)
    setUploadProgress(0)
  }, [])

  return {
    predict,
    clearResult,
    currentResult,
    uploadProgress,
    isPredicting: predictMutation.isPending,
    isSuccess: predictMutation.isSuccess,
    error: predictMutation.error,
  }
}

export const usePredictionHistory = (params: PredictionFilterParams = {}) => {
  return useQuery({
    queryKey: ['predictions', params],
    queryFn: () => predictionsApi.listPredictions(params),
    staleTime: 30 * 1000,
  })
}

export const useDeletePrediction = () => {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: predictionsApi.deletePrediction,
    onSuccess: () => {
      toast.success('Prediction deleted')
      queryClient.invalidateQueries({ queryKey: ['predictions'] })
    },
    onError: () => {
      toast.error('Failed to delete prediction')
    },
  })
}
