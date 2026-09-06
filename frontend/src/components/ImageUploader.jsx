import { useState, useCallback } from 'react'
import { useDropzone } from 'react-dropzone'
import axios from 'axios'
import { X, Upload } from 'lucide-react'

const API_URL = 'http://localhost:8000/api'

export default function ImageUploader({ onImagesUploaded }) {
  const [images, setImages] = useState([])
  const [uploading, setUploading] = useState(false)

  const onDrop = useCallback(async (acceptedFiles) => {
    setUploading(true)
    
    const formData = new FormData()
    acceptedFiles.forEach((file) => {
      formData.append('files', file)
    })

    try {
      const response = await axios.post(`${API_URL}/upload`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      })

      const newImages = response.data.files.map(file => ({
        ...file,
        preview: URL.createObjectURL(acceptedFiles.find(f => f.name === file.original_name))
      }))

      const updatedImages = [...images, ...newImages]
      setImages(updatedImages)
      onImagesUploaded(updatedImages)
    } catch (error) {
      console.error('Upload error:', error)
      alert('Failed to upload images. Please make sure the backend is running and try again.')
    } finally {
      setUploading(false)
    }
  }, [images, onImagesUploaded])

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.tif', '.tiff', '.png', '.jpg', '.jpeg', '.geotiff']
    },
    maxFiles: 4
  })

  const removeImage = (index) => {
    const updatedImages = images.filter((_, i) => i !== index)
    setImages(updatedImages)
    onImagesUploaded(updatedImages)
  }

  return (
    <div className="space-y-3">
      {/* Dropzone */}
      <div
        {...getRootProps()}
        className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-all ${
          isDragActive
            ? 'border-blue-500 bg-blue-50'
            : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50'
        }`}
      >
        <input {...getInputProps()} />
        
        {uploading ? (
          <div className="flex flex-col items-center">
            <div className="animate-spin rounded-full h-8 w-8 border-2 border-blue-600 border-t-transparent"></div>
            <p className="mt-2 text-xs text-gray-600">Uploading...</p>
          </div>
        ) : (
          <div className="flex flex-col items-center">
            <Upload className="w-8 h-8 text-gray-400 mb-2" />
            <p className="text-sm font-medium text-gray-900">
              {isDragActive ? 'Drop images here' : 'Drop satellite images here'}
            </p>
            <p className="text-xs text-gray-500 mt-1">
              or <span className="text-blue-600">click to browse</span>
            </p>
            <p className="text-xs text-gray-400 mt-1">
              GeoTIFF, TIFF, PNG, JPEG • Max 4 images
            </p>
          </div>
        )}
      </div>

      {/* Image Previews - Small Thumbnails */}
      {images.length > 0 && (
        <div className="flex flex-wrap gap-3">
          {images.map((image, index) => (
            <div key={index} className="relative group">
              <div className="w-20 h-20 rounded-lg overflow-hidden border border-gray-200 bg-gray-50">
                <img
                  src={image.preview}
                  alt={image.original_name}
                  className="w-full h-full object-cover"
                />
              </div>
              <div className="mt-1 max-w-20">
                <p className="text-xs text-gray-700 truncate font-medium">
                  {image.original_name}
                </p>
                <p className="text-xs text-gray-500">
                  Image {index + 1}
                </p>
              </div>
              <button
                onClick={(e) => {
                  e.stopPropagation()
                  removeImage(index)
                }}
                className="absolute top-1 right-1 p-0.5 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity hover:bg-red-600"
                aria-label="Remove image"
              >
                <X className="w-3 h-3" />
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload hint */}
      {images.length === 0 && (
        <div className="bg-blue-50 border border-blue-100 rounded-lg p-2.5">
          <p className="text-xs text-blue-800">
            <strong>Tip:</strong> Upload 1 image for VQA or Grounding. Upload 2 images for Change Detection or Optical+SAR analysis.
          </p>
        </div>
      )}
    </div>
  )
}
