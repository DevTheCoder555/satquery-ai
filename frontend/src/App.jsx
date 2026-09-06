import { useState } from 'react'
import ImageUploader from './components/ImageUploader'
import QueryBox from './components/QueryBox'
import ResultPanel from './components/ResultPanel'
import ChatHistory from './components/ChatHistory'
import axios from 'axios'

const API_URL = 'http://localhost:8000/api'

function App() {
  const [uploadedImages, setUploadedImages] = useState([])
  const [query, setQuery] = useState('')
  const [sensorTypes, setSensorTypes] = useState([])
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState(null)
  const [chatHistory, setChatHistory] = useState([])
  const [showChatHistory, setShowChatHistory] = useState(false)

  const handleImagesUploaded = (images) => {
    setUploadedImages(images)
    setError(null)
  }

  const handleAnalyze = async () => {
    if (uploadedImages.length === 0) {
      setError('Please upload at least one image')
      return
    }

    if (!query.trim()) {
      setError('Please enter a question')
      return
    }

    setLoading(true)
    setError(null)
    setResult(null)

    try {
      const response = await axios.post(`${API_URL}/analyze`, {
        query: query,
        image_paths: uploadedImages.map(img => img.path),
        sensor_types: sensorTypes.length > 0 ? sensorTypes : null,
        chat_history: chatHistory
      })

      setResult(response.data)
      
      // Update chat history from response
      if (response.data.chat_history) {
        setChatHistory(response.data.chat_history)
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Analysis failed. Please try again.')
      console.error('Analysis error:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleReset = () => {
    setUploadedImages([])
    setQuery('')
    setSensorTypes([])
    setResult(null)
    setError(null)
    setChatHistory([])
    setShowChatHistory(false)
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-14">
            <div className="flex items-center gap-2">
              <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <h1 className="text-base font-semibold text-gray-900">SatQuery AI</h1>
                <p className="text-xs text-gray-500 hidden sm:block">Satellite Image Analysis</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {chatHistory.length > 0 && (
                <button
                  onClick={() => setShowChatHistory(!showChatHistory)}
                  className="px-3 py-1.5 text-sm font-medium text-blue-600 bg-blue-50 border border-blue-200 rounded-md hover:bg-blue-100 transition-colors"
                >
                  {showChatHistory ? 'Hide' : 'Show'} History ({chatHistory.length})
                </button>
              )}
              {result && (
                <button
                  onClick={handleReset}
                  className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                >
                  New Analysis
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Chat History Panel */}
        {showChatHistory && chatHistory.length > 0 && (
          <div className="mb-4">
            <ChatHistory history={chatHistory} />
          </div>
        )}

        {!result ? (
          <div className="space-y-4">
            {/* Upload Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h2 className="text-sm font-medium text-gray-900 mb-3">
                Upload Satellite Image(s)
              </h2>
              <ImageUploader onImagesUploaded={handleImagesUploaded} />
              
              {uploadedImages.length > 0 && (
                <div className="mt-3 pt-3 border-t border-gray-100">
                  <label className="block text-xs font-medium text-gray-700 mb-2">
                    Sensor Types <span className="text-gray-500">(Optional)</span>
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {uploadedImages.map((img, idx) => (
                      <div key={idx} className="flex items-center gap-2 bg-gray-50 rounded px-2 py-1.5">
                        <span className="text-xs text-gray-600">Image {idx + 1}:</span>
                        <select
                          value={sensorTypes[idx] || ''}
                          onChange={(e) => {
                            const newTypes = [...sensorTypes]
                            newTypes[idx] = e.target.value
                            setSensorTypes(newTypes)
                          }}
                          className="text-xs border border-gray-300 rounded px-2 py-1 focus:outline-none focus:ring-1 focus:ring-blue-500 bg-white"
                        >
                          <option value="">Auto-detect</option>
                          <option value="optical">Optical</option>
                          <option value="sar">SAR</option>
                        </select>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Query Section */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <QueryBox
                query={query}
                setQuery={setQuery}
                onAnalyze={handleAnalyze}
                loading={loading}
                imageCount={uploadedImages.length}
              />
            </div>

            {/* Error Display */}
            {error && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-3">
                <div className="flex items-start gap-2">
                  <svg className="w-4 h-4 text-red-600 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                  <p className="text-sm text-red-800">{error}</p>
                </div>
              </div>
            )}

            {/* Example Queries */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
              <h3 className="text-xs font-medium text-gray-900 mb-2">Try these examples:</h3>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                <button
                  onClick={() => setQuery('What is visible in this image?')}
                  className="text-left text-xs p-2 bg-blue-50 hover:bg-blue-100 rounded transition-colors border border-blue-100"
                >
                  <span className="font-medium text-blue-900">VQA:</span>
                  <span className="text-gray-700 ml-1">"What is visible in this image?"</span>
                </button>
                <button
                  onClick={() => setQuery('Highlight the water body')}
                  className="text-left text-xs p-2 bg-green-50 hover:bg-green-100 rounded transition-colors border border-green-100"
                >
                  <span className="font-medium text-green-900">Grounding:</span>
                  <span className="text-gray-700 ml-1">"Highlight the water body"</span>
                </button>
                <button
                  onClick={() => setQuery('What changed between these two images?')}
                  className="text-left text-xs p-2 bg-purple-50 hover:bg-purple-100 rounded transition-colors border border-purple-100"
                >
                  <span className="font-medium text-purple-900">Change Detection:</span>
                  <span className="text-gray-700 ml-1">"What changed between these images?"</span>
                </button>
                <button
                  onClick={() => setQuery('Use both images to identify built-up regions')}
                  className="text-left text-xs p-2 bg-orange-50 hover:bg-orange-100 rounded transition-colors border border-orange-100"
                >
                  <span className="font-medium text-orange-900">Optical+SAR:</span>
                  <span className="text-gray-700 ml-1">"Use both images to identify built-up regions"</span>
                </button>
              </div>
            </div>
          </div>
        ) : (
          <ResultPanel result={result} images={uploadedImages} />
        )}
      </main>
    </div>
  )
}

export default App
