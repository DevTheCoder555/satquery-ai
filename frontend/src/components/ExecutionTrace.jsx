import { CheckCircle, AlertCircle, Loader2 } from 'lucide-react'

export default function ExecutionTrace({ trace }) {
  if (!trace || trace.length === 0) {
    return null
  }

  const getIcon = (status) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="w-4 h-4 text-green-500" />
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-500" />
      case 'running':
        return <Loader2 className="w-4 h-4 text-blue-500 animate-spin" />
      default:
        return <CheckCircle className="w-4 h-4 text-gray-400" />
    }
  }

  const getBorderColor = (status) => {
    switch (status) {
      case 'success':
        return 'border-green-200 bg-green-50'
      case 'error':
        return 'border-red-200 bg-red-50'
      case 'running':
        return 'border-blue-200 bg-blue-50'
      default:
        return 'border-gray-200 bg-gray-50'
    }
  }

  const successCount = trace.filter(s => s.status === 'success').length

  return (
    <div className="space-y-2">
      {trace.map((step, index) => (
        <div
          key={index}
          className={`flex items-start gap-2 p-2.5 rounded-lg border ${getBorderColor(step.status)}`}
        >
          <div className="flex-shrink-0 mt-0.5">
            {getIcon(step.status)}
          </div>
          <div className="flex-1 min-w-0">
            <div className="flex items-center justify-between gap-2">
              <h4 className="text-xs font-semibold text-gray-900 truncate">{step.step}</h4>
              <span className="text-xs text-gray-500 flex-shrink-0">Step {index + 1}</span>
            </div>
            <p className="text-xs text-gray-600 mt-0.5">{step.message}</p>
          </div>
        </div>
      ))}

      {/* Summary */}
      <div className="mt-3 p-2.5 bg-blue-50 rounded-lg border border-blue-200">
        <div className="flex items-center justify-between">
          <div>
            <p className="text-xs font-medium text-gray-900">Analysis Complete</p>
            <p className="text-xs text-gray-600 mt-0.5">
              {successCount} of {trace.length} steps successful
            </p>
          </div>
          <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
            successCount === trace.length ? 'bg-green-100' : 'bg-yellow-100'
          }`}>
            <span className={`text-sm font-bold ${
              successCount === trace.length ? 'text-green-600' : 'text-yellow-600'
            }`}>
              {successCount === trace.length ? '✓' : '!'}
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
