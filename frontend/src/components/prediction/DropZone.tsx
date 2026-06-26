import { useCallback, useState, useEffect } from 'react'
import { useDropzone } from 'react-dropzone'
import { motion, AnimatePresence } from 'framer-motion'
import { Upload, X, AlertCircle, FileImage } from 'lucide-react'
import { clsx } from 'clsx'
import { validateImageFile } from '@/utils/validators'
import { formatFileSize } from '@/utils/formatters'

interface DropZoneProps {
  onFileSelected?: (file: File) => void
  onFileSelect?: (file: File) => void
  onFileRemoved?: () => void
  selectedFile?: File | null
  previewUrl?: string | null
  isUploading?: boolean
  uploadProgress?: number
  className?: string
  disabled?: boolean
}

export const DropZone: React.FC<DropZoneProps> = ({
  onFileSelected,
  onFileSelect,
  onFileRemoved,
  selectedFile: propSelectedFile,
  previewUrl: propPreviewUrl,
  isUploading = false,
  uploadProgress = 0,
  className,
  disabled = false,
}) => {
  const [error, setError] = useState<string | null>(null)
  const [dragActive, setDragActive] = useState(false)
  
  // Internal state fallback if not managed by parent
  const [internalFile, setInternalFile] = useState<File | null>(null)
  const [internalPreview, setInternalPreview] = useState<string | null>(null)

  const activeFile = propSelectedFile !== undefined ? propSelectedFile : internalFile
  const activePreview = propPreviewUrl !== undefined ? propPreviewUrl : internalPreview

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      setError(null)
      const file = acceptedFiles[0]
      if (!file) return

      const validation = validateImageFile(file)
      if (!validation.isValid) {
        setError(validation.error || 'Invalid file')
        return
      }

      // Update internal state if parent doesn't control it
      if (propSelectedFile === undefined) {
        setInternalFile(file)
        setInternalPreview(URL.createObjectURL(file))
      }

      const selectFn = onFileSelect || onFileSelected
      if (selectFn) selectFn(file)
    },
    [onFileSelect, onFileSelected, propSelectedFile]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/png': ['.png'],
      'image/tiff': ['.tiff', '.tif'],
      'image/bmp': ['.bmp'],
      'image/webp': ['.webp'],
    },
    maxFiles: 1,
    disabled: disabled || isUploading || !!activeFile,
    onDragEnter: () => setDragActive(true),
    onDragLeave: () => setDragActive(false),
  })

  const handleRemove = (e: React.MouseEvent) => {
    e.stopPropagation()
    setError(null)
    
    if (propSelectedFile === undefined) {
      if (internalPreview) URL.revokeObjectURL(internalPreview)
      setInternalFile(null)
      setInternalPreview(null)
    }

    onFileRemoved?.()
  }

  // Cleanup object URL
  useEffect(() => {
    return () => {
      if (internalPreview) {
        URL.revokeObjectURL(internalPreview)
      }
    }
  }, [internalPreview])

  return (
    <div className={clsx('w-full', className)}>
      <AnimatePresence mode="wait">
        {activeFile && activePreview ? (
          // Preview state
          <motion.div
            key="preview"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            className="relative rounded-2xl overflow-hidden border border-white/15 bg-white/5"
          >
            <img
              src={activePreview}
              alt="Preview"
              className="w-full h-64 object-contain bg-black/20"
            />
            {/* File info overlay */}
            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FileImage size={16} className="text-slate-400" />
                  <div>
                    <p className="text-sm font-medium text-white truncate max-w-[200px]">
                      {activeFile.name}
                    </p>
                    <p className="text-xs text-slate-400">
                      {formatFileSize(activeFile.size)}
                    </p>
                  </div>
                </div>
                <button
                  type="button"
                  onClick={handleRemove}
                  className="p-1.5 rounded-lg bg-red-500/20 hover:bg-red-500/30 text-red-400 transition-colors cursor-pointer"
                >
                  <X size={16} />
                </button>
              </div>
            </div>
          </motion.div>
        ) : (
          // Upload state
          <motion.div
            key="upload"
            initial={{ opacity: 0, scale: 0.95 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.95 }}
            {...getRootProps()}
            className={clsx(
              'border-2 border-dashed rounded-2xl p-8 flex flex-col items-center justify-center gap-4 cursor-pointer transition-all duration-300 min-h-64',
              isDragActive
                ? 'border-indigo-500 bg-indigo-500/10'
                : 'border-slate-800 bg-slate-900/40 hover:border-indigo-500/40 hover:bg-slate-800/40'
            )}
          >
            <input {...getInputProps()} />
            
            <motion.div
              animate={isDragActive ? { y: -5 } : {}}
              transition={{ type: 'spring', stiffness: 300, damping: 15 }}
            >
              <Upload size={32} className="text-indigo-400" />
            </motion.div>

            <div className="text-center">
              <p className="text-sm font-semibold text-white">
                {isDragActive ? 'Drop your rock sample image here' : 'Drop rock sample image here'}
              </p>
              <p className="text-xs text-slate-400 mt-1">
                or <span className="text-indigo-400 font-medium">click to browse</span>
              </p>
              <p className="text-[10px] text-slate-500 mt-3">
                Supports: JPEG, PNG, TIFF, BMP, WebP • Max 20MB
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Error message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="flex items-center gap-2 mt-3 p-3 rounded-xl bg-red-500/10 border border-red-500/30"
          >
            <AlertCircle size={16} className="text-red-500 shrink-0" />
            <p className="text-xs text-red-300">{error}</p>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default DropZone
