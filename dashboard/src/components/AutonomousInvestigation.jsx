import { useState, useEffect } from 'react'
import { fetchIntervalSummaries, fetchGeminiQueries } from '../api/client'
import GeminiConversation from './GeminiConversation'
import QueryInvestigation from './QueryInvestigation'

function AutonomousInvestigation() {
  const [summaries, setSummaries] = useState([])
  const [queries, setQueries] = useState([])
  const [selectedSummary, setSelectedSummary] = useState(null)
  const [activeView, setActiveView] = useState('conversation') // 'conversation' or 'query'
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  useEffect(() => {
    loadData()
    const interval = setInterval(loadData, 3000) // Refresh every 3s for live feel
    return () => clearInterval(interval)
  }, [])

  const loadData = async () => {
    try {
      const [summariesData, queriesData] = await Promise.all([
        fetchIntervalSummaries(1000).catch(err => {  // Fetch more to get actual count
          console.error('Summaries error:', err)
          return []
        }),
        fetchGeminiQueries(10000).catch(err => {  // Fetch more to get actual count
          console.error('Queries error:', err)
          return []
        })
      ])
      
      setSummaries(summariesData || [])
      setQueries(queriesData || [])
      setLoading(false)
      setError(null)
    } catch (error) {
      console.error('Failed to load autonomous investigation data:', error)
      setError(error.message)
      setLoading(false)
    }
  }

  const getQueriesForSummary = (summaryId) => {
    const summary = summaries.find(s => s.id === summaryId)
    if (!summary) return []
    
    return queries.filter(q => {
      const qTime = new Date(q.created_at)
      const sTime = new Date(summary.interval_end)
      const diff = Math.abs(qTime - sTime) / 1000 / 60
      return diff < 2
    })
  }

  const parseGeminiResponse = (summary) => {
    try {
      return summary.gemini_response ? JSON.parse(summary.gemini_response) : null
    } catch {
      return null
    }
  }

  const getInvestigationStatus = (summary) => {
    const geminiResponse = parseGeminiResponse(summary)
    const relatedQueries = getQueriesForSummary(summary.id)
    
    if (!summary.sent_to_gemini) {
      return { phase: 'PENDING', label: 'Pending Analysis', color: '#6b7280' }
    }
    
    // Check if Gemini is still requesting more data
    if (geminiResponse && geminiResponse.needs_more_data === true) {
      return { phase: 'QUERYING', label: 'Querying Data', color: '#3b82f6', active: true }
    }
    
    // If we have queries but no response yet, still querying
    if (relatedQueries.length > 0 && !geminiResponse) {
      return { phase: 'QUERYING', label: 'Querying Data', color: '#3b82f6', active: true }
    }
    
    // If we have a response (and needs_more_data is not true), analysis is complete
    if (geminiResponse) {
      const risk = geminiResponse.risk_score || 0
      if (risk > 0.7) {
        return { phase: 'THREAT', label: 'Threat Detected', color: '#ef4444' }
      } else if (risk > 0.4) {
        return { phase: 'SUSPICIOUS', label: 'Suspicious', color: '#f59e0b' }
      } else {
        return { phase: 'BENIGN', label: 'Benign', color: '#10b981' }
      }
    }
    
    return { phase: 'ANALYZING', label: 'Analyzing', color: '#3b82f6', active: true }
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '60px', color: '#9ca3af' }}>
        <div style={{ fontSize: '14px' }}>Loading autonomous investigation data...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div style={{
        background: '#1a1a1a',
        border: '1px solid #ef4444',
        borderRadius: '12px',
        padding: '30px',
        textAlign: 'center'
      }}>
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2" style={{ margin: '0 auto 16px' }}>
          <circle cx="12" cy="12" r="10"/>
          <line x1="12" y1="8" x2="12" y2="12"/>
          <line x1="12" y1="16" x2="12.01" y2="16"/>
        </svg>
        <div style={{ fontSize: '16px', color: '#ef4444', marginBottom: '8px' }}>
          Failed to Load Data
        </div>
        <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '20px' }}>
          {error}
        </div>
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
          Make sure the agent and API server are running
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedSummary ? '1fr 500px' : '1fr', gap: '20px' }}>
      {/* Main List */}
      <div style={{
        background: '#1a1a1a',
        border: '1px solid #2a2a2a',
        borderRadius: '12px',
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{ padding: '24px', borderBottom: '1px solid #2a2a2a' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M12 2L2 7l10 5 10-5-10-5z"/>
              <path d="M2 17l10 5 10-5"/>
              <path d="M2 12l10 5 10-5"/>
            </svg>
            <h2 style={{ fontSize: '20px', fontWeight: '600' }}>
              Autonomous Investigations
            </h2>
          </div>
          <p style={{ fontSize: '13px', color: '#9ca3af' }}>
            Click any interval to see Gemini's live investigation progress
          </p>
        </div>

        {/* Stats */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          gap: '1px',
          background: '#2a2a2a',
          borderBottom: '1px solid #2a2a2a'
        }}>
          <div style={{ background: '#1a1a1a', padding: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#0066cc' }}>
              {summaries.length}
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
              Total Intervals
            </div>
          </div>
          <div style={{ background: '#1a1a1a', padding: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#8b5cf6' }}>
              {summaries.filter(s => s.sent_to_gemini).length}
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
              Analyzed
            </div>
          </div>
          <div style={{ background: '#1a1a1a', padding: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6' }}>
              {queries.length}
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
              Queries Made
            </div>
          </div>
          <div style={{ background: '#1a1a1a', padding: '16px', textAlign: 'center' }}>
            <div style={{ fontSize: '24px', fontWeight: '700', color: '#ef4444' }}>
              {summaries.filter(s => {
                const resp = parseGeminiResponse(s)
                return resp && resp.risk_score > 0.7
              }).length}
            </div>
            <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
              Threats Found
            </div>
          </div>
        </div>

        {/* List */}
        {summaries.length === 0 ? (
          <div style={{ padding: '60px', textAlign: 'center', color: '#9ca3af' }}>
            <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 16px' }}>
              <circle cx="12" cy="12" r="10"/>
              <polyline points="12 6 12 12 16 14"/>
            </svg>
            <div style={{ fontSize: '14px', marginBottom: '8px' }}>
              Waiting for interval summaries...
            </div>
            <div style={{ fontSize: '12px', color: '#6b7280' }}>
              Data collected every 1 minute
            </div>
          </div>
        ) : (
          <div style={{ maxHeight: 'calc(100vh - 400px)', overflowY: 'auto' }}>
            {summaries.map((summary) => {
              const status = getInvestigationStatus(summary)
              const geminiResponse = parseGeminiResponse(summary)
              const relatedQueries = getQueriesForSummary(summary.id)
              const isSelected = selectedSummary?.id === summary.id
              const suspiciousPatterns = JSON.parse(summary.suspicious_patterns || '[]')

              return (
                <div
                  key={summary.id}
                  onClick={() => setSelectedSummary(summary)}
                  style={{
                    padding: '16px 24px',
                    borderBottom: '1px solid #2a2a2a',
                    cursor: 'pointer',
                    background: isSelected ? '#0a0a1a' : 'transparent',
                    transition: 'background 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (!isSelected) e.currentTarget.style.background = '#151515'
                  }}
                  onMouseLeave={(e) => {
                    if (!isSelected) e.currentTarget.style.background = 'transparent'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                      <div style={{
                        width: '8px',
                        height: '8px',
                        borderRadius: '50%',
                        background: status.color,
                        animation: status.active ? 'pulse 2s infinite' : 'none'
                      }} />
                      <span style={{ fontSize: '13px', color: '#9ca3af' }}>
                        {new Date(summary.interval_start).toLocaleTimeString()} - 
                        {new Date(summary.interval_end).toLocaleTimeString()}
                      </span>
                    </div>
                    <span style={{
                      fontSize: '11px',
                      fontWeight: '600',
                      color: status.color,
                      padding: '4px 8px',
                      background: `${status.color}15`,
                      borderRadius: '4px'
                    }}>
                      {status.label}
                    </span>
                  </div>

                  <div style={{ fontSize: '14px', color: '#e0e0e0', marginBottom: '8px' }}>
                    {summary.summary_text}
                  </div>

                  <div style={{ display: 'flex', gap: '16px', fontSize: '12px', color: '#6b7280' }}>
                    <span>{summary.total_processes} processes</span>
                    {relatedQueries.length > 0 && (
                      <span style={{
                        color: '#8b5cf6',
                        background: '#8b5cf620',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: '600'
                      }}>
                        {relatedQueries.length} queries
                      </span>
                    )}
                    {suspiciousPatterns.length > 0 && (
                      <span style={{
                        color: '#f59e0b',
                        background: '#f59e0b20',
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: '600'
                      }}>
                        {suspiciousPatterns.length} suspicious
                      </span>
                    )}
                    {geminiResponse && (
                      <span style={{
                        color: status.color,
                        background: `${status.color}20`,
                        padding: '2px 6px',
                        borderRadius: '4px',
                        fontWeight: '600'
                      }}>
                        Risk: {(geminiResponse.risk_score * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Enhanced Investigation Panel */}
      {selectedSummary && (
        <div style={{
          background: '#1a1a1a',
          border: '1px solid #2a2a2a',
          borderRadius: '12px',
          height: 'calc(100vh - 220px)',
          display: 'flex',
          flexDirection: 'column',
          position: 'sticky',
          top: '20px',
          overflow: 'hidden'
        }}>
          {/* Header */}
          <div style={{
            padding: '20px',
            borderBottom: '1px solid #2a2a2a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between'
          }}>
            <div>
              <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '4px' }}>
                Autonomous Investigation
              </h3>
              <p style={{ fontSize: '12px', color: '#9ca3af' }}>
                {new Date(selectedSummary.interval_start).toLocaleTimeString()} - 
                {new Date(selectedSummary.interval_end).toLocaleTimeString()}
              </p>
            </div>
            <button
              onClick={() => setSelectedSummary(null)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#9ca3af',
                cursor: 'pointer',
                padding: '4px',
                display: 'flex',
                alignItems: 'center'
              }}
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <line x1="18" y1="6" x2="6" y2="18"/>
                <line x1="6" y1="6" x2="18" y2="18"/>
              </svg>
            </button>
          </div>

          {/* View Tabs */}
          <div style={{
            display: 'flex',
            borderBottom: '1px solid #2a2a2a',
            background: '#0a0a0a'
          }}>
            <button
              onClick={() => setActiveView('conversation')}
              style={{
                flex: 1,
                background: activeView === 'conversation' ? '#1a1a1a' : 'transparent',
                border: 'none',
                borderBottom: activeView === 'conversation' ? '2px solid #0066cc' : '2px solid transparent',
                color: activeView === 'conversation' ? '#e0e0e0' : '#6b7280',
                padding: '12px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
              </svg>
              Real-Time
            </button>
            <button
              onClick={() => setActiveView('query')}
              style={{
                flex: 1,
                background: activeView === 'query' ? '#1a1a1a' : 'transparent',
                border: 'none',
                borderBottom: activeView === 'query' ? '2px solid #0066cc' : '2px solid transparent',
                color: activeView === 'query' ? '#e0e0e0' : '#6b7280',
                padding: '12px',
                cursor: 'pointer',
                fontSize: '12px',
                fontWeight: '600',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '6px'
              }}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <circle cx="11" cy="11" r="8"/>
                <path d="m21 21-4.35-4.35"/>
              </svg>
              Query Details
            </button>
          </div>

          {/* View Content */}
          <div style={{ flex: 1, overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
            {activeView === 'conversation' ? (
              <GeminiConversation
                summary={selectedSummary}
                queries={getQueriesForSummary(selectedSummary.id)}
                geminiResponse={parseGeminiResponse(selectedSummary)}
              />
            ) : (
              <QueryInvestigation
                summary={selectedSummary}
                queries={getQueriesForSummary(selectedSummary.id)}
                geminiResponse={parseGeminiResponse(selectedSummary)}
              />
            )}
          </div>
        </div>
      )}
    </div>
  )
}

export default AutonomousInvestigation
