const API_BASE = '/api'

export async function fetchInvestigations() {
  const response = await fetch(`${API_BASE}/investigations/`)
  if (!response.ok) throw new Error('Failed to fetch investigations')
  return response.json()
}

export async function fetchInvestigation(id) {
  const response = await fetch(`${API_BASE}/investigations/${id}`)
  if (!response.ok) throw new Error('Failed to fetch investigation')
  return response.json()
}

export async function fetchEvidence(id, type = null) {
  const url = type 
    ? `${API_BASE}/investigations/${id}/evidence?evidence_type=${type}`
    : `${API_BASE}/investigations/${id}/evidence`
  const response = await fetch(url)
  if (!response.ok) throw new Error('Failed to fetch evidence')
  return response.json()
}

export async function fetchTimeline(id) {
  const response = await fetch(`${API_BASE}/investigations/${id}/timeline`)
  if (!response.ok) throw new Error('Failed to fetch timeline')
  return response.json()
}

export async function fetchAnalysis(id) {
  const response = await fetch(`${API_BASE}/investigations/${id}/analysis`)
  if (!response.ok) throw new Error('Failed to fetch analysis')
  return response.json()
}

export async function addNote(id, note, createdBy = 'analyst') {
  const response = await fetch(`${API_BASE}/investigations/${id}/notes`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ note, created_by: createdBy })
  })
  if (!response.ok) throw new Error('Failed to add note')
  return response.json()
}

export async function closeInvestigation(id) {
  const response = await fetch(`${API_BASE}/investigations/${id}/close`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to close investigation')
  return response.json()
}

export async function fetchConfig() {
  const response = await fetch(`${API_BASE}/config/`)
  if (!response.ok) throw new Error('Failed to fetch config')
  return response.json()
}

export async function updateConfig(updates) {
  const response = await fetch(`${API_BASE}/config/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(updates)
  })
  if (!response.ok) throw new Error('Failed to update config')
  return response.json()
}

export async function fetchProfiles() {
  const response = await fetch(`${API_BASE}/config/profiles`)
  if (!response.ok) throw new Error('Failed to fetch profiles')
  return response.json()
}

export async function applyProfile(profileId) {
  const response = await fetch(`${API_BASE}/config/profiles/${profileId}/apply`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to apply profile')
  return response.json()
}

export async function testGeminiConnection() {
  const response = await fetch(`${API_BASE}/config/test-gemini`, {
    method: 'POST'
  })
  if (!response.ok) throw new Error('Failed to test Gemini connection')
  return response.json()
}

// Autonomous Investigation APIs
export async function fetchIntervalSummaries(limit = 20) {
  const response = await fetch(`${API_BASE}/investigations/intervals/summaries?limit=${limit}`)
  if (!response.ok) throw new Error('Failed to fetch interval summaries')
  return response.json()
}

export async function fetchGeminiQueries(limit = 50) {
  const response = await fetch(`${API_BASE}/investigations/gemini/queries?limit=${limit}`)
  if (!response.ok) throw new Error('Failed to fetch Gemini queries')
  return response.json()
}

export async function fetchRawEvents(pid = null, limit = 100) {
  const params = pid ? `?pid=${pid}&limit=${limit}` : `?limit=${limit}`
  const response = await fetch(`${API_BASE}/investigations/intervals/raw-events${params}`)
  if (!response.ok) throw new Error('Failed to fetch raw events')
  return response.json()
}
