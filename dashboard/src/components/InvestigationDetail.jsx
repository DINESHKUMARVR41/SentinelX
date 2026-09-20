import { useState, useEffect } from 'react'
import { fetchEvidence, fetchAnalysis } from '../api/client'
import EvidenceTimeline from './EvidenceTimeline'
import GeminiReasoning from './GeminiReasoning'
import RiskMeter from './RiskMeter'

function InvestigationDetail({ investigation, onClose }) {
  const [evidence, setEvidence] = useState([])
  const [analysis, setAnalysis] = useState(null)
  const [activeTab, setActiveTab] = useState('overview')
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    loadData()
  }, [investigation.id])

  const loadData = async () => {
    try {
      const [evidenceData, analysisData] = await Promise.all([
        fetchEvidence(investigation.id),
        fetchAnalysis(investigation.id).catch(() => null)
      ])
      setEvidence(evidenceData)
      setAnalysis(analysisData)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load investigation data:', error)
      setLoading(false)
    }
  }

  return (
    <div className="card" style={{ position: 'sticky', top: '20px', maxHeight: 'calc(100vh - 40px)', overflow: 'auto' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '20px' }}>
        <div>
          <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '4px' }}>
            {investigation.process_name}
          </h2>
          <p style={{ color: '#9ca3af', fontSize: '13px' }}>
            PID {investigation.pid} • {investigation.id}
          </p>
        </div>
        <button
          onClick={onClose}
          style={{
            background: 'transparent',
            border: 'none',
            color: '#9ca3af',
            cursor: 'pointer',
            fontSize: '20px'
          }}
        >
          ×
        </button>
      </div>

      {/* Risk Meter */}
      <div style={{ marginBottom: '20px' }}>
        <RiskMeter
          score={investigation.risk_score}
          level={investigation.risk_level}
          confidence={investigation.confidence}
        />
      </div>

      {/* Tabs */}
      <div style={{ borderBottom: '1px solid #2a2a2a', marginBottom: '20px' }}>
        <div style={{ display: 'flex', gap: '0' }}>
          {['overview', 'evidence', 'analysis'].map(tab => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              style={{
                background: 'transparent',
                border: 'none',
                borderBottom: activeTab === tab ? '2px solid #0066cc' : '2px solid transparent',
                color: activeTab === tab ? '#e0e0e0' : '#9ca3af',
                padding: '10px 16px',
                cursor: 'pointer',
                fontSize: '13px',
                fontWeight: '500',
                textTransform: 'capitalize'
              }}
            >
              {tab}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <p style={{ color: '#9ca3af', textAlign: 'center' }}>Loading...</p>
      ) : (
        <>
          {activeTab === 'overview' && (
            <div>
              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                  Process Path
                </label>
                <div style={{ fontSize: '13px', fontFamily: 'monospace', color: '#e0e0e0' }}>
                  {investigation.process_path || 'Unknown'}
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                  Parent Process
                </label>
                <div style={{ fontSize: '13px', color: '#e0e0e0' }}>
                  {investigation.parent_name || 'Unknown'} (PID {investigation.parent_pid || 'N/A'})
                </div>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                  Status
                </label>
                <span className={`status-badge status-${investigation.status.toLowerCase()}`}>
                  {investigation.current_phase}
                </span>
              </div>

              <div style={{ marginBottom: '16px' }}>
                <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                  Triggered At
                </label>
                <div style={{ fontSize: '13px', color: '#e0e0e0' }}>
                  {new Date(investigation.triggered_at).toLocaleString()}
                </div>
              </div>

              {investigation.summary && (
                <div style={{ marginBottom: '16px' }}>
                  <label style={{ fontSize: '12px', color: '#9ca3af', display: 'block', marginBottom: '4px' }}>
                    Summary
                  </label>
                  <div style={{ fontSize: '13px', color: '#e0e0e0' }}>
                    {investigation.summary}
                  </div>
                </div>
              )}
            </div>
          )}

          {activeTab === 'evidence' && (
            <EvidenceTimeline evidence={evidence} />
          )}

          {activeTab === 'analysis' && (
            <GeminiReasoning analysis={analysis} />
          )}
        </>
      )}
    </div>
  )
}

export default InvestigationDetail
