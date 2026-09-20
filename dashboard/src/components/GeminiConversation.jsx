import { useState, useEffect, useRef } from 'react'
import DetailedReportModal from './DetailedReportModal'
import { FileText } from 'lucide-react'
import { Monitor, MessageSquare } from 'lucide-react'

function GeminiConversation({ summary, queries, geminiResponse }) {
  const [autoScroll, setAutoScroll] = useState(true)
  const [showDetailedReport, setShowDetailedReport] = useState(false)
  const conversationEndRef = useRef(null)
  
  // Check if detailed report should be available
  const hasHighRisk = geminiResponse && 
    geminiResponse.risk_score >= 0.5 && 
    (geminiResponse.confidence || 0) >= 0.6

  useEffect(() => {
    if (autoScroll && conversationEndRef.current) {
      conversationEndRef.current.scrollIntoView({ behavior: 'smooth' })
    }
  }, [queries, geminiResponse, autoScroll])

  // Build conversation messages
  const buildConversation = () => {
    const messages = []

    // 1. System sends summary to Gemini
    messages.push({
      id: 'summary_sent',
      role: 'system',
      timestamp: summary.interval_end,
      content: {
        type: 'summary',
        text: 'Sending 1-minute interval summary to Gemini 2.5 Flash for analysis...',
        data: {
          processes: summary.total_processes,
          suspicious: JSON.parse(summary.suspicious_patterns || '[]').length,
          summary: summary.summary_text
        }
      }
    })

    // 2. Gemini's initial thinking
    if (summary.sent_to_gemini) {
      messages.push({
        id: 'gemini_thinking',
        role: 'gemini',
        timestamp: summary.interval_end,
        content: {
          type: 'thinking',
          text: 'Analyzing summary with thinking_level="low" for fast triage...',
          thinking: geminiResponse?.initial_assessment || 'Evaluating patterns and risk indicators'
        }
      })
    }

    // 3. Gemini's queries (conversation turns)
    queries.forEach((query, index) => {
      const params = JSON.parse(query.query_params)
      
      // Gemini asks for data
      messages.push({
        id: `query_request_${query.id}`,
        role: 'gemini',
        timestamp: query.created_at,
        content: {
          type: 'query_request',
          text: `I need more information. Executing ${query.query_type}...`,
          query: {
            action: params.action,
            process_id: params.process_id,
            time_range: params.time_range,
            pattern: params.pattern,
            reasoning: `Query ${index + 1}: Investigating ${query.query_type.replace('QUERY_', '').toLowerCase()}`
          }
        }
      })

      // System responds with data
      if (query.result_count > 0) {
        messages.push({
          id: `query_response_${query.id}`,
          role: 'system',
          timestamp: query.created_at,
          content: {
            type: 'query_response',
            text: `Returned ${query.result_count} results from raw database`,
            data: {
              count: query.result_count,
              query_type: query.query_type
            }
          }
        })
      }
    })

    // 4. Gemini's deep analysis (if queries were made)
    if (geminiResponse && queries.length > 0) {
      messages.push({
        id: 'deep_analysis',
        role: 'gemini',
        timestamp: queries[queries.length - 1]?.created_at || summary.interval_end,
        content: {
          type: 'analysis',
          text: 'Re-analyzing with query results using thinking_level="high"...',
          analysis: geminiResponse.summary || 'Performing comprehensive analysis with collected evidence'
        }
      })
    }

    // 5. Final verdict
    if (geminiResponse) {
      const riskLevel = geminiResponse.risk_score > 0.7 ? 'HIGH' :
                       geminiResponse.risk_score > 0.4 ? 'MEDIUM' : 'LOW'
      
      // Use confidence from Gemini AI (required field)
      // If Gemini didn't provide confidence, use 0.0 to indicate missing data
      let confidence = geminiResponse.confidence
      if (confidence === undefined || confidence === null) {
        console.warn('Warning: Gemini did not provide confidence value, using 0.0')
        confidence = 0.0
      }
      
      messages.push({
        id: 'verdict',
        role: 'gemini',
        timestamp: summary.interval_end,
        content: {
          type: 'verdict',
          text: `Investigation complete. Risk level: ${riskLevel}`,
          verdict: {
            risk_score: geminiResponse.risk_score,
            confidence: confidence,
            classification: geminiResponse.classification,
            reasoning: geminiResponse.reasoning,
            threats: geminiResponse.threats_identified || []
          }
        }
      })
    }

    return messages
  }

  const messages = buildConversation()

  const getRoleColor = (role) => {
    switch (role) {
      case 'system': return '#3b82f6'
      case 'gemini': return '#8b5cf6'
      default: return '#6b7280'
    }
  }

  const getRoleIcon = (role) => {
    if (role === 'system') {
      return <Monitor size={16} />
    } else {
      return <MessageSquare size={16} />
    }
  }

  const renderMessageContent = (content) => {
    switch (content.type) {
      case 'summary':
        return (
          <div>
            <div style={{ marginBottom: '8px' }}>{content.text}</div>
            <div style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px'
            }}>
              <div style={{ marginBottom: '4px' }}>
                <span style={{ color: '#6b7280' }}>Processes:</span> {content.data.processes}
              </div>
              <div style={{ marginBottom: '4px' }}>
                <span style={{ color: '#6b7280' }}>Suspicious:</span> {content.data.suspicious}
              </div>
              <div style={{ color: '#9ca3af', marginTop: '8px', fontStyle: 'italic' }}>
                "{content.data.summary}"
              </div>
            </div>
          </div>
        )

      case 'thinking':
        return (
          <div>
            <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                border: '2px solid #8b5cf6',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              {content.text}
            </div>
            <div style={{
              background: '#8b5cf615',
              border: '1px solid #8b5cf630',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px',
              color: '#c4b5fd',
              fontStyle: 'italic'
            }}>
              {content.thinking}
            </div>
          </div>
        )

      case 'query_request':
        return (
          <div>
            <div style={{ marginBottom: '8px', fontWeight: '600' }}>{content.text}</div>
            <div style={{
              background: '#8b5cf615',
              border: '1px solid #8b5cf630',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px'
            }}>
              <div style={{ marginBottom: '6px', color: '#c4b5fd' }}>
                {content.query.reasoning}
              </div>
              <div style={{ color: '#9ca3af' }}>
                <div><span style={{ color: '#6b7280' }}>Action:</span> {content.query.action}</div>
                {content.query.process_id && (
                  <div><span style={{ color: '#6b7280' }}>Process:</span> {content.query.process_id}</div>
                )}
                {content.query.time_range && (
                  <div><span style={{ color: '#6b7280' }}>Time Range:</span> {content.query.time_range}</div>
                )}
                {content.query.pattern && (
                  <div><span style={{ color: '#6b7280' }}>Pattern:</span> {content.query.pattern}</div>
                )}
              </div>
            </div>
          </div>
        )

      case 'query_response':
        return (
          <div>
            <div style={{ marginBottom: '8px' }}>{content.text}</div>
            <div style={{
              background: '#3b82f615',
              border: '1px solid #3b82f630',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px',
              color: '#93c5fd'
            }}>
              ✓ Query executed successfully
              <div style={{ marginTop: '4px', color: '#9ca3af' }}>
                {content.data.count} records retrieved from {content.data.query_type}
              </div>
            </div>
          </div>
        )

      case 'analysis':
        return (
          <div>
            <div style={{ marginBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <div style={{
                width: '12px',
                height: '12px',
                border: '2px solid #8b5cf6',
                borderTopColor: 'transparent',
                borderRadius: '50%',
                animation: 'spin 1s linear infinite'
              }} />
              {content.text}
            </div>
            <div style={{
              background: '#8b5cf615',
              border: '1px solid #8b5cf630',
              borderRadius: '6px',
              padding: '10px',
              fontSize: '11px',
              color: '#c4b5fd',
              fontStyle: 'italic'
            }}>
              {content.analysis}
            </div>
          </div>
        )

      case 'verdict':
        const riskColor = content.verdict.risk_score > 0.7 ? '#ef4444' :
                         content.verdict.risk_score > 0.4 ? '#f59e0b' : '#10b981'
        
        return (
          <div>
            <div style={{ marginBottom: '12px', fontWeight: '600', fontSize: '13px' }}>
              {content.text}
            </div>
            <div style={{
              background: `${riskColor}15`,
              border: `1px solid ${riskColor}30`,
              borderRadius: '6px',
              padding: '12px',
              fontSize: '11px'
            }}>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', marginBottom: '12px' }}>
                <div>
                  <div style={{ color: '#6b7280', marginBottom: '2px' }}>Risk Score</div>
                  <div style={{ color: riskColor, fontWeight: '700', fontSize: '16px' }}>
                    {(content.verdict.risk_score * 100).toFixed(0)}%
                  </div>
                </div>
                <div>
                  <div style={{ color: '#6b7280', marginBottom: '2px' }}>Confidence</div>
                  <div style={{ color: riskColor, fontWeight: '700', fontSize: '16px' }}>
                    {(content.verdict.confidence * 100).toFixed(0)}%
                  </div>
                </div>
              </div>
              
              {content.verdict.classification && (
                <div style={{ marginBottom: '8px' }}>
                  <span style={{ color: '#6b7280' }}>Classification:</span>{' '}
                  <span style={{ color: riskColor }}>{content.verdict.classification}</span>
                </div>
              )}
              
              {content.verdict.reasoning && (
                <div style={{ color: '#9ca3af', marginTop: '8px', fontStyle: 'italic' }}>
                  {content.verdict.reasoning}
                </div>
              )}

              {content.verdict.threats.length > 0 && (
                <div style={{ marginTop: '12px', paddingTop: '12px', borderTop: `1px solid ${riskColor}30` }}>
                  <div style={{ color: riskColor, fontWeight: '600', marginBottom: '6px' }}>
                    Threats Identified: {content.verdict.threats.length}
                  </div>
                  {content.verdict.threats.map((threat, i) => (
                    <div key={i} style={{
                      background: '#0a0a0a',
                      padding: '8px',
                      borderRadius: '4px',
                      marginBottom: '6px'
                    }}>
                      <div style={{ color: riskColor, fontWeight: '600', fontSize: '11px' }}>
                        {threat.threat_type}
                      </div>
                      <div style={{ color: '#9ca3af', fontSize: '10px' }}>
                        {threat.process_name} (PID: {threat.pid})
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )

      default:
        return <div>{content.text}</div>
    }
  }

  return (
    <>
      {showDetailedReport && (
        <DetailedReportModal 
          investigationId={summary.id}
          summaryData={summary}
          geminiResponse={geminiResponse}
          onClose={() => setShowDetailedReport(false)} 
        />
      )}
      
      <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header Controls */}
      <div style={{
        padding: '12px 16px',
        borderBottom: '1px solid #2a2a2a',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between'
      }}>
        <div style={{ fontSize: '12px', color: '#9ca3af' }}>
          {messages.length} messages
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          {hasHighRisk && (
            <button
              onClick={() => setShowDetailedReport(true)}
              className="button button-primary"
              style={{
                padding: '6px 12px',
                fontSize: '11px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}
            >
              <FileText size={14} />
              View Detailed Report
            </button>
          )}
          <label style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', color: '#9ca3af', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={autoScroll}
              onChange={(e) => setAutoScroll(e.target.checked)}
              style={{ cursor: 'pointer' }}
            />
            Auto-scroll
          </label>
        </div>
      </div>

      {/* Conversation */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '16px'
      }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
          {messages.map((message) => (
            <div key={message.id} style={{
              display: 'flex',
              gap: '12px',
              alignItems: 'flex-start'
            }}>
              {/* Avatar */}
              <div style={{
                width: '32px',
                height: '32px',
                borderRadius: '8px',
                background: `${getRoleColor(message.role)}20`,
                border: `1px solid ${getRoleColor(message.role)}40`,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: getRoleColor(message.role),
                flexShrink: 0
              }}>
                {getRoleIcon(message.role)}
              </div>

              {/* Message */}
              <div style={{ flex: 1, minWidth: 0 }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  marginBottom: '6px'
                }}>
                  <span style={{
                    fontSize: '12px',
                    fontWeight: '600',
                    color: getRoleColor(message.role)
                  }}>
                    {message.role === 'system' ? 'SentinelX Agent' : 'Gemini 2.5 Flash'}
                  </span>
                  <span style={{ fontSize: '10px', color: '#6b7280' }}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </span>
                </div>
                <div style={{
                  fontSize: '12px',
                  color: '#e0e0e0',
                  lineHeight: '1.5'
                }}>
                  {renderMessageContent(message.content)}
                </div>
              </div>
            </div>
          ))}
          <div ref={conversationEndRef} />
        </div>
      </div>
    </div>
    </>
  )
}

export default GeminiConversation
