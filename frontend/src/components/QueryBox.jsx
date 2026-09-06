import { Send, Loader2 } from 'lucide-react'

export default function QueryBox({ query, setQuery, onAnalyze, loading, imageCount }) {
  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      onAnalyze()
    }
  }

  return (
    <div className="space-y-3">
      <div>
        <label htmlFor="query" className="block text-sm font-medium text-gray-900 mb-1.5">
          Ask your question
        </label>
        <p className="text-xs text-gray-500 mb-2">
          {imageCount === 0 && 'Upload an image to get started'}
          {imageCount === 1 && 'Ask anything about your satellite image'}
          {imageCount >= 2 && 'Ask about changes, comparisons, or combined analysis'}
        </p>
        <textarea
          id="query"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyPress}
          placeholder={
            imageCount === 0
              ? 'Upload an image first...'
              : imageCount === 1
              ? 'e.g., "What is visible in this image?" or "Highlight the water body"'
              : 'e.g., "What changed between these images?" or "Use both to identify built-up areas"'
          }
          rows={3}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none text-sm transition-shadow"
          disabled={loading || imageCount === 0}
        />
      </div>

      <button
        onClick={onAnalyze}
        disabled={loading || !query.trim() || imageCount === 0}
        className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {loading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            <span>Analyzing...</span>
          </>
        ) : (
          <>
            <Send className="w-4 h-4" />
            <span>Analyze</span>
          </>
        )}
      </button>
    </div>
  )
}
