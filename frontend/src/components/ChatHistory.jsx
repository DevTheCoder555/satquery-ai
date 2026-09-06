import { MessageSquare, User, Bot } from 'lucide-react'

export default function ChatHistory({ history }) {
  if (!history || history.length === 0) {
    return null
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
      <h3 className="text-sm font-semibold text-gray-900 mb-3 flex items-center gap-2">
        <MessageSquare className="w-4 h-4 text-blue-600" />
        Conversation History
      </h3>
      <div className="space-y-2 max-h-64 overflow-y-auto">
        {history.map((msg, index) => (
          <div
            key={index}
            className={`flex items-start gap-2 p-2 rounded-lg ${
              msg.role === 'user' ? 'bg-blue-50' : 'bg-green-50'
            }`}
          >
            <div className="flex-shrink-0 mt-0.5">
              {msg.role === 'user' ? (
                <User className="w-4 h-4 text-blue-600" />
              ) : (
                <Bot className="w-4 h-4 text-green-600" />
              )}
            </div>
            <div className="flex-1 min-w-0">
              {msg.role === 'user' ? (
                <div>
                  <p className="text-xs font-medium text-gray-700">You</p>
                  <p className="text-xs text-gray-900 mt-0.5">{msg.query}</p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Task: {msg.task_type?.replace('_', ' ').toUpperCase()}
                  </p>
                </div>
              ) : (
                <div>
                  <p className="text-xs font-medium text-gray-700">AI Assistant</p>
                  <p className="text-xs text-gray-900 mt-0.5 line-clamp-2">
                    {msg.answer}
                  </p>
                  <p className="text-xs text-gray-500 mt-0.5">
                    Confidence: {(msg.confidence * 100).toFixed(1)}%
                  </p>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
