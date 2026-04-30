import React, { useState, useEffect } from 'react'
import {
  ArrowLeft, Rocket, Cloud, Server, CheckCircle2,
  AlertTriangle, XCircle, Loader2, Download, FileText
} from 'lucide-react'
import { validateDeployment, triggerDeployment, getDnaData } from '../services/api'

const PLATFORMS = [
  { id: 'azure', name: 'Microsoft Azure', desc: 'Primary cloud with full ADAM governance plane', icon: Cloud },
  { id: 'aws', name: 'Amazon Web Services', desc: 'Warm standby or primary alternative', icon: Cloud },
  { id: 'gcp', name: 'Google Cloud Platform', desc: 'Full GCP-native deployment', icon: Cloud },
  { id: 'k8s', name: 'Open Source Kubernetes', desc: 'Deploy on any K8s cluster (EKS, GKE, AKS, bare metal)', icon: Server },
  { id: 'azure-local', name: 'Azure Local (On-Premises)', desc: 'Sovereign on-premises failover with Azure Stack HCI', icon: Server },
]

export default function DeployPanel({ sessionId, progress, onBack }) {
  const [selectedPlatforms, setSelectedPlatforms] = useState(['azure', 'aws'])
  const [includeDocx, setIncludeDocx] = useState(true)
  const [includeIac, setIncludeIac] = useState(true)
  const [includeConfig, setIncludeConfig] = useState(true)
  const [validation, setValidation] = useState(null)
  const [deploying, setDeploying] = useState(false)
  const [result, setResult] = useState(null)

  useEffect(() => {
    if (sessionId) {
      validateDeployment(sessionId).then(setValidation).catch(console.error)
    }
  }, [sessionId])

  const togglePlatform = (id) => {
    setSelectedPlatforms(prev =>
      prev.includes(id) ? prev.filter(p => p !== id) : [...prev, id]
    )
  }

  const handleDeploy = async () => {
    if (!selectedPlatforms.length) return
    setDeploying(true)
    try {
      const res = await triggerDeployment(sessionId, selectedPlatforms, {
        includeDocx, includeIac, includeConfig,
      })
      setResult(res)
    } catch (err) {
      setResult({ success: false, error: err.message })
    } finally {
      setDeploying(false)
    }
  }

  const handleDownloadDna = async () => {
    try {
      const dna = await getDnaData(sessionId)
      const blob = new Blob([JSON.stringify(dna, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `adam-dna-${dna.meta?.company_name || 'config'}.json`
      a.click()
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  return (
    <div className="flex-1 overflow-y-auto bg-gray-50 p-6">
      <div className="max-w-3xl mx-auto">
        {/* Header */}
        <div className="flex items-center gap-3 mb-6">
          <button onClick={onBack} className="p-2 hover:bg-gray-200 rounded-lg transition-colors">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h2 className="text-xl font-bold text-gray-900">Generate ADAM Deployment</h2>
            <p className="text-sm text-gray-500">Configure and trigger deployment artifact generation</p>
          </div>
        </div>

        {/* Validation Status */}
        {validation && (
          <div className={`rounded-xl p-4 mb-6 ${
            validation.valid ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center gap-2 mb-2">
              {validation.valid
                ? <CheckCircle2 className="w-5 h-5 text-green-600" />
                : <XCircle className="w-5 h-5 text-red-600" />
              }
              <span className={`font-semibold ${validation.valid ? 'text-green-800' : 'text-red-800'}`}>
                {validation.valid ? 'DNA Ready for Deployment' : 'DNA Validation Issues'}
              </span>
              <span className="text-sm text-gray-500 ml-auto">
                {validation.completion_pct}% complete ({validation.total_answered}/{validation.total_questions})
              </span>
            </div>
            {validation.issues?.length > 0 && (
              <ul className="mt-2 space-y-1">
                {validation.issues.map((issue, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-red-700">
                    <XCircle className="w-3.5 h-3.5" /> {issue}
                  </li>
                ))}
              </ul>
            )}
            {validation.warnings?.length > 0 && (
              <ul className="mt-2 space-y-1">
                {validation.warnings.map((warn, i) => (
                  <li key={i} className="flex items-center gap-2 text-sm text-amber-700">
                    <AlertTriangle className="w-3.5 h-3.5" /> {warn}
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}

        {/* Platform Selection */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">Target Platforms</h3>
          <div className="space-y-2">
            {PLATFORMS.map(({ id, name, desc, icon: Icon }) => (
              <label
                key={id}
                className={`flex items-center gap-3 p-3 rounded-lg cursor-pointer transition-colors ${
                  selectedPlatforms.includes(id)
                    ? 'bg-adam-50 border border-adam-200'
                    : 'bg-gray-50 border border-transparent hover:border-gray-200'
                }`}
              >
                <input
                  type="checkbox"
                  checked={selectedPlatforms.includes(id)}
                  onChange={() => togglePlatform(id)}
                  className="rounded border-gray-300 text-adam-600 focus:ring-adam-500"
                />
                <Icon className={`w-5 h-5 ${selectedPlatforms.includes(id) ? 'text-adam-600' : 'text-gray-400'}`} />
                <div>
                  <div className="text-sm font-medium text-gray-900">{name}</div>
                  <div className="text-xs text-gray-500">{desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Output Options */}
        <div className="bg-white rounded-xl border border-gray-200 p-5 mb-6">
          <h3 className="font-semibold text-gray-900 mb-3">Output Artifacts</h3>
          <div className="space-y-2">
            {[
              { key: 'iac', label: 'Infrastructure-as-Code', desc: 'Terraform, Bicep, CloudFormation, Helm', checked: includeIac, set: setIncludeIac },
              { key: 'config', label: 'Configuration Bundle', desc: 'CORE Graph seeds, BOSS policies, agent registry, schemas', checked: includeConfig, set: setIncludeConfig },
              { key: 'docx', label: 'Word Documents', desc: 'Professional deployment specifications per platform', checked: includeDocx, set: setIncludeDocx },
            ].map(({ key, label, desc, checked, set }) => (
              <label key={key} className="flex items-center gap-3 p-3 rounded-lg bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={(e) => set(e.target.checked)}
                  className="rounded border-gray-300 text-adam-600 focus:ring-adam-500"
                />
                <div>
                  <div className="text-sm font-medium text-gray-900">{label}</div>
                  <div className="text-xs text-gray-500">{desc}</div>
                </div>
              </label>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          <button
            onClick={handleDownloadDna}
            className="flex items-center gap-2 px-4 py-2.5 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 text-sm font-medium transition-colors"
          >
            <Download className="w-4 h-4" />
            Download DNA JSON
          </button>

          <button
            onClick={handleDeploy}
            disabled={deploying || !selectedPlatforms.length || (validation && !validation.valid)}
            className="flex-1 flex items-center justify-center gap-2 px-4 py-2.5 bg-adam-600 text-white rounded-lg hover:bg-adam-700 disabled:opacity-50 disabled:cursor-not-allowed text-sm font-medium transition-colors"
          >
            {deploying ? (
              <><Loader2 className="w-4 h-4 animate-spin" /> Generating...</>
            ) : (
              <><Rocket className="w-4 h-4" /> Generate Deployment Artifacts</>
            )}
          </button>
        </div>

        {/* Result */}
        {result && (
          <div className={`mt-6 rounded-xl p-5 ${
            result.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'
          }`}>
            <div className="flex items-center gap-2 mb-3">
              {result.success
                ? <CheckCircle2 className="w-6 h-6 text-green-600" />
                : <XCircle className="w-6 h-6 text-red-600" />
              }
              <span className={`font-semibold text-lg ${result.success ? 'text-green-800' : 'text-red-800'}`}>
                {result.success ? 'Deployment Artifacts Generated' : 'Generation Failed'}
              </span>
            </div>

            {result.success && (
              <div className="space-y-2 text-sm text-green-800">
                <p>Platforms: {result.platforms?.join(', ')}</p>
                <p>Files generated: {result.files_generated}</p>
                <p>Output: {result.output_dir}</p>
                {result.artifacts?.length > 0 && (
                  <div className="mt-3 max-h-40 overflow-y-auto">
                    {result.artifacts.slice(0, 20).map((a, i) => (
                      <div key={i} className="flex items-center gap-2 py-0.5">
                        <FileText className="w-3.5 h-3.5" />
                        <span className="truncate">{a.path || a.description}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {result.error && (
              <p className="text-sm text-red-700">{result.error}</p>
            )}

            {result.message && (
              <p className="text-sm text-gray-600 mt-2">{result.message}</p>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
