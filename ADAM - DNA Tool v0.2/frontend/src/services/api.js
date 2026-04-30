/**
 * ADAM DNA Tool - API Service Layer
 * Handles all communication with the FastAPI backend.
 */

const API_BASE = '/api';

class APIError extends Error {
  constructor(message, status, data) {
    super(message);
    this.status = status;
    this.data = data;
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };

  const response = await fetch(url, config);

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new APIError(
      data.detail || `Request failed: ${response.status}`,
      response.status,
      data
    );
  }

  return response.json();
}

// Session
export async function createSession(aiProvider = 'openai', companyName = '') {
  return request('/sessions', {
    method: 'POST',
    body: JSON.stringify({ ai_provider: aiProvider, company_name: companyName }),
  });
}

export async function getSession(sessionId) {
  return request(`/sessions/${sessionId}`);
}

export async function getMessages(sessionId, limit = 50, offset = 0) {
  return request(`/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`);
}

// Conversation
export async function sendMessage(sessionId, message) {
  return request(`/sessions/${sessionId}/messages`, {
    method: 'POST',
    body: JSON.stringify({ message }),
  });
}

export async function uploadDocument(sessionId, file) {
  const formData = new FormData();
  formData.append('file', file);

  const url = `${API_BASE}/sessions/${sessionId}/upload`;
  const response = await fetch(url, { method: 'POST', body: formData });

  if (!response.ok) {
    const data = await response.json().catch(() => ({}));
    throw new APIError(data.detail || 'Upload failed', response.status, data);
  }

  return response.json();
}

export async function fetchUrl(sessionId, url) {
  return request(`/sessions/${sessionId}/fetch-url`, {
    method: 'POST',
    body: JSON.stringify({ url }),
  });
}

// Phase & Progress
export async function advancePhase(sessionId, targetPhase = null) {
  return request(`/sessions/${sessionId}/advance-phase`, {
    method: 'POST',
    body: JSON.stringify({ target_phase: targetPhase }),
  });
}

export async function getProgress(sessionId) {
  return request(`/sessions/${sessionId}/progress`);
}

// DNA Data
export async function getDnaData(sessionId) {
  return request(`/sessions/${sessionId}/dna`);
}

export async function updateDna(sessionId, updates) {
  return request(`/sessions/${sessionId}/dna/update`, {
    method: 'POST',
    body: JSON.stringify({ updates }),
  });
}

export async function getReview(sessionId) {
  return request(`/sessions/${sessionId}/review`);
}

// Deployment
export async function triggerDeployment(sessionId, platforms, options = {}) {
  return request(`/sessions/${sessionId}/deploy`, {
    method: 'POST',
    body: JSON.stringify({
      platforms,
      include_docx: options.includeDocx !== false,
      include_iac: options.includeIac !== false,
      include_config: options.includeConfig !== false,
    }),
  });
}

export async function validateDeployment(sessionId) {
  return request(`/sessions/${sessionId}/deploy/validate`, { method: 'POST' });
}

// Documents
export async function getDocuments(sessionId) {
  return request(`/sessions/${sessionId}/documents`);
}

// Health
export async function getHealth() {
  return request('/health');
}

export async function getAppInfo() {
  return request('/info');
}

// WebSocket
export function createWebSocket(sessionId) {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const wsUrl = `${protocol}//${window.location.host}/api/ws/${sessionId}`;
  return new WebSocket(wsUrl);
}
