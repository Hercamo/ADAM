import React, { useState, useEffect, useCallback } from 'react'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import ChatPanel from './components/ChatPanel'
import DeployPanel from './components/DeployPanel'
import { createSession, getSession } from './services/api'

const PHASES = [
  { key: 'welcome', label: 'Welcome', section: null },
  { key: 'document_ingestion', label: 'Document Ingestion', section: null },
  { key: 'doctrine_identity', label: '1. Doctrine Identity', section: '1' },
  { key: 'culture_graph', label: '2. Culture Graph', section: '2' },
  { key: 'objectives_graph', label: '3. Objectives Graph', section: '3' },
  { key: 'rules_expectations', label: '4. Rules & Expectations', section: '4' },
  { key: 'enterprise_memory', label: '5. Enterprise Memory', section: '5' },
  { key: 'boss_scoring', label: '6. BOSS Scoring', section: '6' },
  { key: 'intent_conflict', label: '7. Intent & Conflict', section: '7' },
  { key: 'agentic_architecture', label: '8. Agent Architecture', section: '8' },
  { key: 'flight_recorder', label: '9. Flight Recorder', section: '9' },
  { key: 'products_services', label: '10. Products & Services', section: '10' },
  { key: 'temporal_regional', label: '11. Temporal & Regional', section: '11' },
  { key: 'cloud_infrastructure', label: '12. Cloud Infrastructure', section: '12' },
  { key: 'resilience_security', label: '13. Resilience & Security', section: '13' },
  { key: 'review_validate', label: 'Review & Validate', section: null },
  { key: 'deployment_ready', label: 'Deploy', section: null },
]

export default function App() {
  const [sessionId, setSessionId] = useState(null)
  const [sessionData, setSessionData] = useState(null)
  const [messages, setMessages] = useState([])
  const [progress, setProgress] = useState(null)
  const [currentPhase, setCurrentPhase] = useState('welcome')
  const [documents, setDocuments] = useState([])
  const [loading, setLoading] = useState(false)
  const [showDeploy, setShowDeploy] = useState(false)
  const [aiProvider, setAiProvider] = useState('openai')

  // Initialize session
  const initSession = useCallback(async (provider = 'openai') => {
    try {
      setLoading(true)
      const result = await createSession(provider)
      setSessionId(result.session_id)
      setMessages([{
        id: 'welcome',
        role: 'assistant',
        content: result.welcome_message,
        type: 'text',
        timestamp: new Date().toISOString(),
      }])
      setCurrentPhase('document_ingestion')
    } catch (err) {
      console.error('Failed to create session:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  // Refresh session data
  const refreshSession = useCallback(async () => {
    if (!sessionId) return
    try {
      const data = await getSession(sessionId)
      setSessionData(data)
      setProgress(data.progress)
      setCurrentPhase(data.current_phase)
    } catch (err) {
      console.error('Failed to refresh session:', err)
    }
  }, [sessionId])

  // Update state from API response
  const handleApiResponse = useCallback((response) => {
    if (response.message) {
      setMessages(prev => [...prev, response.message])
    }
    if (response.progress) {
      setProgress(response.progress)
    }
    if (response.current_phase) {
      setCurrentPhase(response.current_phase)
    }
    if (response.documents) {
      setDocuments(response.documents)
    }
  }, [])

  useEffect(() => {
    initSession(aiProvider)
  }, [])

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      <Header
        sessionId={sessionId}
        companyName={sessionData?.company_name}
        overallProgress={progress?.overall_completion_pct || 0}
        aiProvider={aiProvider}
        onProviderChange={(p) => {
          setAiProvider(p)
          initSession(p)
        }}
      />

      <div className="flex-1 flex overflow-hidden">
        {/* Sidebar - Progress Tracker */}
        <Sidebar
          phases={PHASES}
          currentPhase={currentPhase}
          sectionProgress={sessionData?.section_progress || {}}
          documents={documents}
          onPhaseClick={(phase) => setCurrentPhase(phase)}
          onDeployClick={() => setShowDeploy(true)}
        />

        {/* Main Content */}
        <div className="flex-1 flex flex-col">
          {showDeploy ? (
            <DeployPanel
              sessionId={sessionId}
              progress={progress}
              onBack={() => setShowDeploy(false)}
            />
          ) : (
            <ChatPanel
              sessionId={sessionId}
              messages={messages}
              setMessages={setMessages}
              loading={loading}
              setLoading={setLoading}
              onApiResponse={handleApiResponse}
              currentPhase={currentPhase}
            />
          )}
        </div>
      </div>
    </div>
  )
}
