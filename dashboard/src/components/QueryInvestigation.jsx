import { useState } from 'react'
import { BarChart3, Search, Clock, Network, FileText, AlertTriangle, Zap, CheckCircle, HelpCircle } from 'lucide-react'

function QueryInvestigation({ summary, queries, geminiResponse }) {
  const [selectedQuery, setSelectedQuery] = useState(null)
  const [expandedSection, setExpandedSection] = useState('overview')

  // Parse query details
  const parseQueryDetails = (query) => {
    const params = JSON.parse(query.query_params)
    const result = query.result_data ? JSON.parse(query.result_data) : null
    
    return {
      id: query.id,
      type: query.query_type,
      timestamp: query.created_at,
      params,
      result,
      resultCount: query.result_count || 0,
      executionTime: query.execution_time_ms || 0
    }
  }

  const queryDetails = queries.map(parseQueryDetails)

  // Build investigation flow
  const buildInvestigationFlow = () => {
    const steps = []

    // Step 1: Initial Summary
    steps.push({
      id: 'summary',
      title: 'Initial Summary Analysis',
      icon: 'BarChart3',
      color: '#3b82f6',
      data: {
        processes: summary.total_processes,
        suspicious: JSON.parse(summary.suspicious_patterns || '[]').length,
        highCpu: JSON.parse(summary.high_cpu_processes || '[]').length,
        highNetwork: JSON.parse(summary.high_network_processes || '[]').length
      }
    })

    // Step 2-N: Each query
    queryDetails.forEach((query, index) => {
      const queryType = query.type.replace('QUERY_', '')
      const icons = {
        'PROCESS': 'Search',
        'TIMERANGE': 'Clock',
        'PATTERN': 'Search',
        'NETWORK': 'Network',
        'FILES': 'FileText'
      }

      steps.push({
        id: `query_${query.id}`,
        title: `Query ${index + 1}: ${queryType}`,
        icon: icons[queryType] || 'HelpCircle',
        color: '#8b5cf6',
        query: query
      })
    })

    // Final step: Verdict
    if (geminiResponse) {
      const riskColor = geminiResponse.risk_score > 0.7 ? '#ef4444' :
                       geminiResponse.risk_score > 0.4 ? '#f59e0b' : '#10b981'
      
      steps.push({
        id: 'verdict',
        title: 'Final Verdict',
        icon: geminiResponse.risk_score > 0.7 ? 'AlertTriangle' : geminiResponse.risk_score > 0.4 ? 'Zap' : 'CheckCircle',
        color: riskColor,
        verdict: geminiResponse
      })
    }

    return steps
  }

  const investigationFlow = buildInvestigationFlow()

  const getIconComponent = (iconName) => {
    const icons = {
      'BarChart3': BarChart3,
      'Search': Search,
      'Clock': Clock,
      'Network': Network,
      'FileText': FileText,
      'AlertTriangle': AlertTriangle,
      'Zap': Zap,
      'CheckCircle': CheckCircle,
      'HelpCircle': HelpCircle
    }
    const IconComponent = icons[iconName] || HelpCircle
    return <IconComponent size={20} />
  }

  const renderQueryDetails = (query) => {
    return (
      <div style={{
        background: '#0a0a0a',
        border: '1px solid #2a2a2a',
        borderRadius: '8px',
        padding: '16px'
      }}>
        {/* Query Header */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          marginBottom: '16px',
          paddingBottom: '12px',
          borderBottom: '1px solid #2a2a2a'
        }}>
          <div>
            <div style={{ fontSize: '14px', fontWeight: '600', color: '#8b5cf6', marginBottom: '4px' }}>
              {query.type}
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280' }}>
              {new Date(query.timestamp).toLocaleString()}
            </div>
          </div>
          <div style={{
            background: '#8b5cf620',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '11px',
            color: '#c4b5fd'
          }}>
            {query.resultCount} results
          </div>
        </div>

        {/* Query Parameters */}
        <div style={{ marginBottom: '16px' }}>
          <div style={{
            fontSize: '11px',
            fontWeight: '600',
            color: '#9ca3af',
            marginBottom: '8px',
            textTransform: 'uppercase',
            letterSpacing: '0.5px'
          }}>
            Query Parameters
          </div>
          <div style={{
            background: '#1a1a1a',
            border: '1px solid #2a2a2a',
            borderRadius: '6px',
            padding: '10px',
            fontSize: '11px',
            fontFamily: 'monospace'
          }}>
            {Object.entries(query.params).map(([key, value]) => (
              <div key={key} style={{ marginBottom: '4px' }}>
                <span style={{ color: '#6b7280' }}>{key}:</span>{' '}
                <span style={{ color: '#e0e0e0' }}>
                  {typeof value === 'object' ? JSON.stringify(value) : value}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Query Results */}
        {query.result && (
          <div>
            <div style={{
              fontSize: '11px',
              fontWeight: '600',
              color: '#9ca3af',
              marginBottom: '8px',
              textTransform: 'uppercase',
              letterSpacing: '0.5px'
            }}>
              Results ({query.resultCount} records)
            </div>
            <div style={{
              background: '#1a1a1a',
              border: '1px solid #2a2a2a',
              borderRadius: '6px',
              padding: '10px',
              maxHeight: '300px',
              overflowY: 'auto',
              fontSize: '11px'
            }}>
              {Array.isArray(query.result) ? (
                query.result.slice(0, 10).map((item, i) => (
                  <div key={i} style={{
                    background: '#0a0a0a',
                    padding: '8px',
                    borderRadius: '4px',
                    marginBottom: '6px',
                    border: '1px solid #2a2a2a'
                  }}>
                    {Object.entries(item).map(([key, value]) => (
                      <div key={key} style={{ marginBottom: '2px' }}>
                        <span style={{ color: '#6b7280' }}>{key}:</span>{' '}
                        <span style={{ color: '#9ca3af' }}>
                          {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                        </span>
                      </div>
                    ))}
                  </div>
                ))
              ) : (
                <pre style={{ margin: 0, color: '#9ca3af', whiteSpace: 'pre-wrap' }}>
                  {JSON.stringify(query.result, null, 2)}
                </pre>
              )}
              {query.resultCount > 10 && (
                <div style={{ textAlign: 'center', color: '#6b7280', marginTop: '8px' }}>
                  ... and {query.resultCount - 10} more records
                </div>
              )}
            </div>
          </div>
        )}

        {/* Execution Stats */}
        <div style={{
          marginTop: '12px',
          paddingTop: '12px',
          borderTop: '1px solid #2a2a2a',
          display: 'flex',
          gap: '16px',
          fontSize: '11px',
          color: '#6b7280'
        }}>
          <div>
            <span style={{ color: '#9ca3af' }}>Execution Time:</span> {query.executionTime}ms
          </div>
          <div>
            <span style={{ color: '#9ca3af' }}>Records:</span> {query.resultCount}
          </div>
        </div>
      </div>
    )
  }

  const renderOverview = () => {
    return (
      <div style={{ padding: '16px' }}>
        {/* Investigation Flow */}
        <div style={{ marginBottom: '24px' }}>
          <h4 style={{ fontSize: '13px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Investigation Flow
          </h4>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {investigationFlow.map((step, index) => (
              <div key={step.id}>
                <div
                  onClick={() => {
                    if (step.query) {
                      setSelectedQuery(step.query)
                      setExpandedSection('query')
                    }
                  }}
                  style={{
                    background: '#0a0a0a',
                    border: `1px solid ${step.color}40`,
                    borderRadius: '8px',
                    padding: '12px',
                    cursor: step.query ? 'pointer' : 'default',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    if (step.query) e.currentTarget.style.background = '#151515'
                  }}
                  onMouseLeave={(e) => {
                    if (step.query) e.currentTarget.style.background = '#0a0a0a'
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
                    <div style={{
                      width: '32px',
                      height: '32px',
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      background: `${step.color}20`,
                      borderRadius: '6px',
                      color: step.color
                    }}>
                      {getIconComponent(step.icon)}
                    </div>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontSize: '12px', fontWeight: '600', color: step.color, marginBottom: '2px' }}>
                        Step {index + 1}: {step.title}
                      </div>
                      {step.data && (
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>
                          {step.data.processes} processes • {step.data.suspicious} suspicious patterns
                        </div>
                      )}
                      {step.query && (
                        <div style={{ fontSize: '11px', color: '#6b7280' }}>
                          {step.query.resultCount} results • {step.query.executionTime}ms
                        </div>
                      )}
                      {step.verdict && (
                        <div style={{ fontSize: '11px', color: step.color }}>
                          Risk: {(step.verdict.risk_score * 100).toFixed(0)}% • 
                          Confidence: {((step.verdict.confidence || 0) * 100).toFixed(0)}%
                        </div>
                      )}
                    </div>
                    {step.query && (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2">
                        <polyline points="9 18 15 12 9 6"/>
                      </svg>
                    )}
                  </div>
                </div>
                {index < investigationFlow.length - 1 && (
                  <div style={{
                    width: '2px',
                    height: '12px',
                    background: '#2a2a2a',
                    marginLeft: '16px'
                  }} />
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Summary Stats */}
        <div>
          <h4 style={{ fontSize: '13px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Investigation Statistics
          </h4>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '12px'
          }}>
            <div style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              padding: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#8b5cf6', marginBottom: '4px' }}>
                {queries.length}
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                Queries Executed
              </div>
            </div>
            <div style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              padding: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#3b82f6', marginBottom: '4px' }}>
                {queryDetails.reduce((sum, q) => sum + q.resultCount, 0)}
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                Total Records
              </div>
            </div>
            <div style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              padding: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: '#10b981', marginBottom: '4px' }}>
                {queryDetails.reduce((sum, q) => sum + q.executionTime, 0)}ms
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                Total Time
              </div>
            </div>
            <div style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '8px',
              padding: '12px',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '24px', fontWeight: '700', color: geminiResponse?.risk_score > 0.7 ? '#ef4444' : '#10b981', marginBottom: '4px' }}>
                {geminiResponse ? (geminiResponse.risk_score * 100).toFixed(0) : 0}%
              </div>
              <div style={{ fontSize: '11px', color: '#6b7280' }}>
                Risk Score
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Section Tabs */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #2a2a2a',
        background: '#0a0a0a'
      }}>
        <button
          onClick={() => setExpandedSection('overview')}
          style={{
            flex: 1,
            background: expandedSection === 'overview' ? '#1a1a1a' : 'transparent',
            border: 'none',
            borderBottom: expandedSection === 'overview' ? '2px solid #8b5cf6' : '2px solid transparent',
            color: expandedSection === 'overview' ? '#e0e0e0' : '#6b7280',
            padding: '12px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: '600'
          }}
        >
          Overview
        </button>
        <button
          onClick={() => setExpandedSection('query')}
          style={{
            flex: 1,
            background: expandedSection === 'query' ? '#1a1a1a' : 'transparent',
            border: 'none',
            borderBottom: expandedSection === 'query' ? '2px solid #8b5cf6' : '2px solid transparent',
            color: expandedSection === 'query' ? '#e0e0e0' : '#6b7280',
            padding: '12px',
            cursor: 'pointer',
            fontSize: '12px',
            fontWeight: '600'
          }}
        >
          Query Details
        </button>
      </div>

      {/* Content */}
      <div style={{ flex: 1, overflowY: 'auto' }}>
        {expandedSection === 'overview' && renderOverview()}
        
        {expandedSection === 'query' && (
          <div style={{ padding: '16px' }}>
            {queryDetails.length === 0 ? (
              <div style={{ textAlign: 'center', padding: '40px', color: '#6b7280' }}>
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ margin: '0 auto 12px' }}>
                  <circle cx="11" cy="11" r="8"/>
                  <path d="m21 21-4.35-4.35"/>
                </svg>
                <div style={{ fontSize: '13px' }}>No queries executed yet</div>
              </div>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                {/* Query Selector */}
                <div>
                  <label style={{ fontSize: '11px', color: '#9ca3af', marginBottom: '6px', display: 'block' }}>
                    Select Query
                  </label>
                  <select
                    value={selectedQuery?.id || queryDetails[0]?.id}
                    onChange={(e) => {
                      const query = queryDetails.find(q => q.id === parseInt(e.target.value))
                      setSelectedQuery(query)
                    }}
                    style={{
                      width: '100%',
                      background: '#0a0a0a',
                      border: '1px solid #2a2a2a',
                      borderRadius: '6px',
                      padding: '8px',
                      color: '#e0e0e0',
                      fontSize: '12px',
                      cursor: 'pointer'
                    }}
                  >
                    {queryDetails.map((query, index) => (
                      <option key={query.id} value={query.id}>
                        Query {index + 1}: {query.type} ({query.resultCount} results)
                      </option>
                    ))}
                  </select>
                </div>

                {/* Selected Query Details */}
                {(selectedQuery || queryDetails[0]) && renderQueryDetails(selectedQuery || queryDetails[0])}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}

export default QueryInvestigation
