import React from 'react'
import { Settings, Cpu, Zap } from 'lucide-react'

export default function Header({ sessionId, companyName, overallProgress, aiProvider, onProviderChange }) {
  return (
    <header className="bg-white border-b border-gray-200 px-6 py-3 flex items-center justify-between shrink-0">
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2">
          <Cpu className="w-7 h-7 text-adam-600" />
          <div>
            <h1 className="text-lg font-bold text-gray-900 leading-tight">ADAM DNA Tool</h1>
            <p className="text-xs text-gray-500">Autonomy Doctrine & Architecture Model</p>
          </div>
        </div>
        {companyName && (
          <span className="ml-4 px-3 py-1 bg-adam-50 text-adam-700 rounded-full text-sm font-medium">
            {companyName}
          </span>
        )}
      </div>

      <div className="flex items-center gap-4">
        {/* Progress Bar */}
        <div className="flex items-center gap-2">
          <span className="text-sm text-gray-600">DNA Progress</span>
          <div className="w-40 h-2.5 bg-gray-200 rounded-full overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-adam-500 to-adam-600 rounded-full transition-all duration-500"
              style={{ width: `${overallProgress}%` }}
            />
          </div>
          <span className="text-sm font-semibold text-adam-700">{overallProgress}%</span>
        </div>

        {/* AI Provider Selector */}
        <div className="flex items-center gap-1.5 text-sm">
          <Zap className="w-4 h-4 text-gray-400" />
          <select
            value={aiProvider}
            onChange={(e) => onProviderChange(e.target.value)}
            className="bg-gray-100 border-0 rounded-md px-2 py-1 text-sm text-gray-700 focus:ring-2 focus:ring-adam-300"
          >
            <option value="openai">OpenAI GPT-4o</option>
            <option value="anthropic">Anthropic Claude</option>
            <option value="azure_openai">Azure OpenAI</option>
          </select>
        </div>
      </div>
    </header>
  )
}
