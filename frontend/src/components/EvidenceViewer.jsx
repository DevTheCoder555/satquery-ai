import { useState } from 'react'

// FastAPI backend origin
const API_ORIGIN ='https://satquery-ai-wfb8.onrender.com'

/**
 * Converts the URL returned by the backend into a browser-accessible URL.
 *
 * Supports:
 *   "/api/evidence/change_map.png"
 *   "/evidence/change_map.png"
 *   "/static/change_map.png"
 *   "http://localhost:8000/evidence/change_map.png"
 */
function getImageUrl(url) {
  if (!url) return ''

  // Already a complete URL
  if (url.startsWith('http://') || url.startsWith('https://')) {
    return url
  }

  // Backend already returned /api/...
  if (url.startsWith('/api/')) {
    return `${API_ORIGIN}${url}`
  }

  // Backend returned /uploads/...
  if (url.startsWith('/uploads/')) {
    return `${API_ORIGIN}/api${url}`
  }

  // Filename only
  return `${API_ORIGIN}/api/${url}`
}

export default function EvidenceViewer({ evidenceImages }) {
  const [selectedImage, setSelectedImage] = useState(0)
  const [imageErrors, setImageErrors] = useState({})

  // No evidence available
  if (!evidenceImages || evidenceImages.length === 0) {
    return null
  }

  // Make sure selected index is valid
  const safeIndex =
    selectedImage >= 0 && selectedImage < evidenceImages.length
      ? selectedImage
      : 0

  const selectedEvidence = evidenceImages[safeIndex]

  if (!selectedEvidence) {
    return null
  }

  const selectedUrl = getImageUrl(selectedEvidence.url)

  const handleImageError = (index, url) => {
    console.error('❌ Evidence image failed to load')
    console.error('Original URL:', url)
    console.error('Final URL:', getImageUrl(url))

    setImageErrors((prev) => ({
      ...prev,
      [index]: true,
    }))
  }

  const handleImageLoad = (index, url) => {
    console.log('✅ Evidence image loaded successfully')
    console.log('Image URL:', getImageUrl(url))

    setImageErrors((prev) => ({
      ...prev,
      [index]: false,
    }))
  }

  const formatType = (type) => {
    if (!type) {
      return 'EVIDENCE'
    }

    return type
      .replace(/_/g, ' ')
      .toUpperCase()
  }

  return (
    <div className="space-y-3">

      {/* Main Image Display */}
      <div className="rounded-lg overflow-hidden border border-gray-200 bg-gray-50">

        {imageErrors[safeIndex] ? (
          <div className="flex flex-col items-center justify-center min-h-[250px] p-6 text-center">

            <div className="text-4xl mb-3">
              🖼️
            </div>

            <p className="text-sm font-medium text-red-600">
              Unable to load visual evidence
            </p>

            <p className="text-xs text-gray-500 mt-2 break-all">
              {selectedUrl}
            </p>

            <button
              type="button"
              onClick={() => {
                setImageErrors((prev) => ({
                  ...prev,
                  [safeIndex]: false,
                }))
              }}
              className="mt-4 px-3 py-1.5 text-xs border border-gray-300 rounded-md hover:bg-gray-100"
            >
              Retry
            </button>

          </div>
        ) : (
          <img
            src={selectedUrl}
            alt={
              selectedEvidence.description ||
              'Visual evidence'
            }
            className="w-full h-auto max-h-[600px] object-contain"
            onError={() =>
              handleImageError(
                safeIndex,
                selectedEvidence.url
              )
            }
            onLoad={() =>
              handleImageLoad(
                safeIndex,
                selectedEvidence.url
              )
            }
          />
        )}

        {/* Image Information */}
        <div className="p-2.5 bg-white border-t border-gray-100">

          <p className="text-xs text-gray-700">
            {selectedEvidence.description ||
              'Visual evidence'}
          </p>

          <p className="text-xs text-gray-500 mt-0.5">
            Type:{' '}
            {formatType(selectedEvidence.type)}
          </p>

          {/* Useful for debugging */}
          <p className="text-[10px] text-gray-400 mt-1 break-all">
            Source: {selectedUrl}
          </p>

        </div>
      </div>

      {/* Thumbnail Navigation */}
      {evidenceImages.length > 1 && (
        <div className="grid grid-cols-3 sm:grid-cols-4 gap-2">

          {evidenceImages.map((image, index) => {
            const imageUrl = getImageUrl(image.url)

            return (
              <button
                type="button"
                key={`${image.url}-${index}`}
                onClick={() => setSelectedImage(index)}
                className={`
                  rounded-lg
                  overflow-hidden
                  border-2
                  transition-all
                  bg-gray-50
                  ${
                    selectedImage === index
                      ? 'border-blue-500 ring-2 ring-blue-200'
                      : 'border-gray-200 hover:border-gray-300'
                  }
                `}
              >

                {imageErrors[index] ? (
                  <div className="h-20 flex items-center justify-center text-xs text-red-500">
                    Image unavailable
                  </div>
                ) : (
                  <img
                    src={imageUrl}
                    alt={
                      image.description ||
                      `Evidence ${index + 1}`
                    }
                    className="w-full h-20 object-cover"
                    onError={() =>
                      handleImageError(
                        index,
                        image.url
                      )
                    }
                    onLoad={() =>
                      handleImageLoad(
                        index,
                        image.url
                      )
                    }
                  />
                )}

              </button>
            )
          })}

        </div>
      )}

      {/* Debug Information */}
      <details className="text-xs text-gray-500">
        <summary className="cursor-pointer hover:text-gray-700">
          Debug evidence data
        </summary>

        <pre className="mt-2 p-3 bg-gray-100 rounded-md overflow-auto">
          {JSON.stringify(
            evidenceImages,
            null,
            2
          )}
        </pre>
      </details>

    </div>
  )
}