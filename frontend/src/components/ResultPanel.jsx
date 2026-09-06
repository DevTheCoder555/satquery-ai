import { CheckCircle, Download, Clock, Cpu } from 'lucide-react'
import EvidenceViewer from './EvidenceViewer'
import ExecutionTrace from './ExecutionTrace'

export default function ResultPanel({ result, images }) {
  const handleDownloadReport = () => {
    const report = {
      task_type: result.task_type,
      answer: result.answer,
      confidence: result.confidence,
      model_used: result.model_used,
      response_time: result.response_time,
      execution_trace: result.execution_trace,
      timestamp: new Date().toISOString()
    }

    const blob = new Blob([JSON.stringify(report, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `satquery-report-${Date.now()}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  const getTaskBadgeColor = (taskType) => {
    switch (taskType) {
      case 'vqa': return 'bg-blue-100 text-blue-700 border-blue-200'
      case 'grounding': return 'bg-green-100 text-green-700 border-green-200'
      case 'change_detection': return 'bg-purple-100 text-purple-700 border-purple-200'
      case 'optical_sar': return 'bg-orange-100 text-orange-700 border-orange-200'
      default: return 'bg-gray-100 text-gray-700 border-gray-200'
    }
  }

  return (
    <div className="space-y-4">
      {/* Result Header */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-2 mb-3">
          <div>
            <h2 className="text-base font-semibold text-gray-900 mb-1.5">Analysis Result</h2>
            <div className="flex flex-wrap gap-2">
              <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium border ${getTaskBadgeColor(result.task_type)}`}>
                {result.task_type.replace('_', ' ').toUpperCase()}
              </span>
              {result.model_used && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                  <Cpu className="w-3 h-3" />
                  {result.model_used}
                </span>
              )}
              {result.response_time && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-medium bg-gray-100 text-gray-700 border border-gray-200">
                  <Clock className="w-3 h-3" />
                  {result.response_time}s
                </span>
              )}
            </div>
          </div>
          <button
            onClick={handleDownloadReport}
            className="flex items-center justify-center gap-1.5 px-3 py-1.5 text-xs font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Download Report</span>
          </button>
        </div>

        {/* Answer */}
        <div className="bg-blue-50 rounded-lg p-3 mb-3 border border-blue-100">
          <p className="text-sm text-gray-900 leading-relaxed">{result.answer}</p>
        </div>

        {/* Confidence */}
        <div>
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-medium text-gray-700">Confidence</span>
            <span className="text-xs font-bold text-gray-900">
              {(result.confidence * 100).toFixed(1)}%
            </span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-blue-600 h-2 rounded-full transition-all duration-500"
              style={{ width: `${result.confidence * 100}%` }}
            ></div>
          </div>
        </div>
      </div>

      {/* Evidence Images */}
      {result.evidence_images && result.evidence_images.length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
          <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-1.5">
            <CheckCircle className="w-4 h-4 text-green-500" />
            Visual Evidence
          </h3>
          <EvidenceViewer evidenceImages={result.evidence_images} />
        </div>
      )}

      {/* Original Images */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Input Images</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {images.map((image, index) => (
            <div key={index} className="rounded-lg overflow-hidden border border-gray-200">
              <img
                src={image.preview}
                alt={image.original_name}
                className="w-full h-auto object-contain max-h-64"
              />
              <div className="p-2 bg-gray-50 border-t border-gray-100">
                <p className="text-xs text-gray-600 truncate">{image.original_name}</p>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Execution Trace */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
        <h3 className="text-sm font-semibold text-gray-900 mb-3">Execution Trace</h3>
        <ExecutionTrace trace={result.execution_trace} />
      </div>
    </div>
  )
}
