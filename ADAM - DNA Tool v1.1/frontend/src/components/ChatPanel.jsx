import React, { useState, useRef, useEffect, useCallback } from 'react'
import ReactMarkdown from 'react-markdown'
import { Send, Upload, Link2, Loader2, Bot, User, Paperclip } from 'lucide-react'
import { sendMessage, uploadDocument, fetchUrl } from '../services/api'

function ChatMessage({ message }) {
  const isAssistant = message.role === 'assistant'

  return (
    <div className={`flex gap-3 px-6 py-4 ${isAssistant ? 'bg-white' : 'bg-gray-50'}`}>
      <div className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 ${
        isAssistant ? 'bg-adam-100 text-adam-600' : 'bg-gray-200 text-gray-600'
      }`}>
        {isAssistant ? <Bot className="w-5 h-5" /> : <User className="w-5 h-5" />}
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-gray-400 mb-1">
          {isAssistant ? 'ADAM DNA Assistant' : 'You'}
          {message.timestamp && (
            <span className="ml-2">
              {new Date(message.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
            </span>
          )}
        </div>
        <div className="chat-message-markdown text-gray-800 text-sm leading-relaxed">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
      </div>
    </div>
  )
}

export default function ChatPanel({ sessionId, messages, setMessages, loading, setLoading, onApiResponse, currentPhase }) {
  const [input, setInput] = useState('')
  const [urlMode, setUrlMode] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const messagesEndRef = useRef(null)
  const fileInputRef = useRef(null)
  const inputRef = useRef(null)

  // Auto-scroll
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Focus input
  useEffect(() => {
    inputRef.current?.focus()
  }, [loading])

  const handleSend = useCallback(async () => {
    if (!input.trim() || !sessionId || loading) return

    const userMessage = input.trim()
    setInput('')
    setLoading(true)

    // Add user message optimistically
    setMessages(prev => [...prev, {
      id: Date.now().toString(),
      role: 'user',
      content: userMessage,
      type: 'text',
      timestamp: new Date().toISOString(),
    }])

    try {
      if (urlMode && userMessage.startsWith('http')) {
        const response = await fetchUrl(sessionId, userMessage)
        onApiResponse(response)
        setUrlMode(false)
      } else {
        const response = await sendMessage(sessionId, userMessage)
        onApiResponse(response)
      }
    } catch (err) {
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Something went wrong: ${err.message}. Please try again.`,
        type: 'error',
        timestamp: new Date().toISOString(),
      }])
    } finally {
      setLoading(false)
    }
  }, [input, sessionId, loading, urlMode, setMessages, setLoading, onApiResponse])

  const handleFileUpload = useCallback(async (files) => {
    if (!sessionId || !files.length) return

    for (const file of files) {
      setLoading(true)
      setMessages(prev => [...prev, {
        id: Date.now().toString(),
        role: 'user',
        content: `Uploading: ${file.name} (${(file.size / 1024).toFixed(1)} KB)`,
        type: 'document_upload',
        timestamp: new Date().toISOString(),
      }])

      try {
        const response = await uploadDocument(sessionId, file)
        onApiResponse(response)
      } catch (err) {
        setMessages(prev => [...prev, {
          id: Date.now().toString(),
          role: 'assistant',
          content: `Failed to process ${file.name}: ${err.message}`,
          type: 'error',
          timestamp: new Date().toISOString(),
        }])
      } finally {
        setLoading(false)
      }
    }
  }, [sessionId, setMessages, setLoading, onApiResponse])

  const handleDrop = useCallback((e) => {
    e.preventDefault()
    setDragActive(false)
    const files = Array.from(e.dataTransfer.files)
    if (files.length) handleFileUpload(files)
  }, [handleFileUpload])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div
      className="flex-1 flex flex-col bg-gray-50"
      onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
      onDragLeave={() => setDragActive(false)}
      onDrop={handleDrop}
    >
      {/* Drag overlay */}
      {dragActive && (
        <div className="absolute inset-0 z-50 bg-adam-500/10 border-2 border-dashed border-adam-400 rounded-lg flex items-center justify-center">
          <div className="bg-white px-8 py-6 rounded-xl shadow-lg text-center">
            <Upload className="w-10 h-10 text-adam-500 mx-auto mb-2" />
            <p className="text-lg font-medium text-gray-800">Drop files to analyze</p>
            <p className="text-sm text-gray-500">DOCX, PPTX, PDF, CSV, JSON, XLSX</p>
          </div>
        </div>
      )}

      {/* Messages */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {messages.map((msg) => (
          <ChatMessage key={msg.id} message={msg} />
        ))}
        {loading && (
          <div className="flex gap-3 px-6 py-4 bg-white">
            <div className="w-8 h-8 rounded-lg bg-adam-100 flex items-center justify-center">
              <Loader2 className="w-5 h-5 text-adam-600 animate-spin" />
            </div>
            <div className="flex items-center">
              <span className="text-sm text-gray-400">Analyzing...</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="border-t border-gray-200 bg-white p-4">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-end gap-2">
            {/* File Upload Button */}
            <button
              onClick={() => fileInputRef.current?.click()}
              className="p-2.5 text-gray-400 hover:text-adam-600 hover:bg-adam-50 rounded-lg transition-colors"
              title="Upload document"
            >
              <Paperclip className="w-5 h-5" />
            </button>
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".docx,.pptx,.pdf,.csv,.json,.xlsx,.txt,.md,.yaml,.yml"
              multiple
              onChange={(e) => handleFileUpload(Array.from(e.target.files))}
            />

            {/* URL Mode Toggle */}
            <button
              onClick={() => setUrlMode(!urlMode)}
              className={`p-2.5 rounded-lg transition-colors ${
                urlMode ? 'text-adam-600 bg-adam-50' : 'text-gray-400 hover:text-adam-600 hover:bg-adam-50'
              }`}
              title="Fetch from URL"
            >
              <Link2 className="w-5 h-5" />
            </button>

            {/* Text Input */}
            <div className="flex-1 relative">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={
                  urlMode
                    ? 'Paste a URL to fetch data from...'
                    : 'Tell me about your company, ask questions, or describe your requirements...'
                }
                rows={1}
                className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 text-sm focus:outline-none focus:ring-2 focus:ring-adam-300 focus:border-transparent"
                style={{ minHeight: '44px', maxHeight: '120px' }}
                disabled={loading}
              />
            </div>

            {/* Send Button */}
            <button
              onClick={handleSend}
              disabled={!input.trim() || loading}
              className="p-2.5 bg-adam-600 text-white rounded-xl hover:bg-adam-700 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>

          <p className="text-xs text-gray-400 mt-2 text-center">
            Upload strategy docs, org charts, financial reports, or compliance documents.
            Drag & drop files anywhere, or paste URLs for remote data.
          </p>
        </div>
      </div>
    </div>
  )
}
