import React from 'react'
import {
  CheckCircle2, Circle, PlayCircle, FileText, Rocket,
  ChevronRight, Upload, Globe, Shield, Brain, BarChart3,
  Layers, Target, Scale, Database, Clock, Cloud, Lock
} from 'lucide-react'

const SECTION_ICONS = {
  'welcome': Globe,
  'document_ingestion': Upload,
  'doctrine_identity': Shield,
  'culture_graph': Brain,
  'objectives_graph': Target,
  'rules_expectations': Scale,
  'enterprise_memory': Database,
  'boss_scoring': BarChart3,
  'intent_conflict': Layers,
  'agentic_architecture': Brain,
  'flight_recorder': FileText,
  'products_services': Globe,
  'temporal_regional': Clock,
  'cloud_infrastructure': Cloud,
  'resilience_security': Lock,
  'review_validate': CheckCircle2,
  'deployment_ready': Rocket,
}

function getStatusIcon(status, completionPct) {
  if (completionPct >= 100) return <CheckCircle2 className="w-4 h-4 text-green-500" />
  if (status === 'in_progress' || completionPct > 0) return <PlayCircle className="w-4 h-4 text-adam-500" />
  return <Circle className="w-4 h-4 text-gray-300" />
}

export default function Sidebar({ phases, currentPhase, sectionProgress, documents, onPhaseClick, onDeployClick }) {
  return (
    <aside className="w-72 bg-white border-r border-gray-200 flex flex-col shrink-0 overflow-hidden">
      {/* Phase Navigation */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-3">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
          Configuration Phases
        </h2>

        <nav className="space-y-0.5">
          {phases.map((phase) => {
            const progress = sectionProgress[phase.key] || {}
            const isActive = currentPhase === phase.key
            const Icon = SECTION_ICONS[phase.key] || Circle
            const pct = progress.completion_pct || 0

            return (
              <button
                key={phase.key}
                onClick={() => onPhaseClick(phase.key)}
                className={`w-full flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-colors text-sm ${
                  isActive
                    ? 'bg-adam-50 text-adam-800 font-medium'
                    : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className={`w-4 h-4 shrink-0 ${isActive ? 'text-adam-600' : 'text-gray-400'}`} />
                <span className="flex-1 truncate">{phase.label}</span>
                <div className="flex items-center gap-1">
                  {phase.section && pct > 0 && pct < 100 && (
                    <span className="text-xs text-gray-400">{Math.round(pct)}%</span>
                  )}
                  {getStatusIcon(progress.status, pct)}
                </div>
              </button>
            )
          })}
        </nav>
      </div>

      {/* Documents Panel */}
      {documents.length > 0 && (
        <div className="border-t border-gray-200 p-3">
          <h3 className="text-xs font-semibold text-gray-400 uppercase tracking-wider px-2 mb-2">
            Documents ({documents.length})
          </h3>
          <div className="space-y-1 max-h-32 overflow-y-auto custom-scrollbar">
            {documents.map((doc) => (
              <div key={doc.id} className="flex items-center gap-2 px-2 py-1 text-xs text-gray-600 truncate">
                <FileText className="w-3.5 h-3.5 text-gray-400 shrink-0" />
                <span className="truncate">{doc.filename}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Deploy Button */}
      <div className="border-t border-gray-200 p-3">
        <button
          onClick={onDeployClick}
          className="w-full flex items-center justify-center gap-2 px-4 py-2.5 bg-adam-600 hover:bg-adam-700 text-white rounded-lg font-medium text-sm transition-colors"
        >
          <Rocket className="w-4 h-4" />
          Generate Deployment
          <ChevronRight className="w-4 h-4" />
        </button>
      </div>
    </aside>
  )
}
