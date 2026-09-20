import { useState } from 'react'

function LiveInvestigationSidebar({ summary, queries, geminiResponse, onClose }) {
  const [expandedTask, setExpandedTask] = useState(null)

  // Build investigation timeline/tasks
  const buildInvestigationTasks = () => {
    const tasks = []
    
    // Task 1: Initial Detection
    tasks.push({
      id: 'detection',
      title: 'Initial Detection',
      status: 'completed',
      timestamp: summary.interval_start,
      details: [
        `Monitored ${summary.total_processes} processes`,
        `Detected ${JSON.parse(summary.suspicious_patterns || '[]').length} suspicious patterns`,
        `Collected raw events for 1-minute interval`
      ]
    })

    // Task 2: Summary Generation
    tasks.push({
      id: 'summary',
      title: 'Generated Summary',
      status: 'completed',
      timestamp: summary.interval_end,
      details: [
        summary.summary_text,
        `High CPU: ${JSON.parse(summary.high_cpu_processes || '[]').length} processes`,
        `Network Activity: ${JSON.parse(summary.high_network_processes || '[]').length} processes`
      ]
    })

    // Task 3: Gemini Initial Analysis
    if (summary.sent_to_gemini) {
      tasks.push({
        id: 'initial_analysis',
        title: 'Gemini Initial Analysis',
        status: geminiResponse ? 'completed' : 'active',
        timestamp: summary.interval_end,
        details: geminiResponse ? [
          `Risk Score: ${(geminiResponse.risk_score * 100).toFixed(0)}%`,
          `Confidence: ${((geminiResponse.confidence || 0) * 100).toFixed(0)}%`,
          geminiResponse.initial_assessment || 'Analysis complete'
        ] : [
          'Analyzing summary with Gemini 2.5 Flash...',
          'Using thinking_level="low" for fast triage',
          'Evaluating suspicious patterns'
        ]
      })
    }

    // Task 4: Autonomous Queries
    if (queries.length > 0) {
      queries.forEach((query, index) => {
        const params = JSON.parse(query.query_params)
        tasks.push({
          id: `query_${query.id}`,
          title: `Query ${index + 1}: ${query.query_type}`,
          status: query.result_count > 0 ? 'completed' : 'active',
          timestamp: query.created_at,
          details: [
            `Action: ${params.action}`,
            params.process_id ? `Process ID: ${params.process_id}` : null,
            params.time_range ? `Time Range: ${params.time_range}` : null,
            params.pattern ? `Pattern: ${params.pattern}` : null,
            query.result_count > 0 ? `✓ Returned ${query.result_count} results` : 'Executing query...'
          ].filter(Boolean)
        })
      })

      // Task 5: Deep Analysis (if queries were made)
      if (geminiResponse && queries.length > 0) {
        tasks.push({
          id: 'deep_analysis',
          title: 'Deep Analysis with Query Results',
          status: 'completed',
          timestamp: queries[queries.length - 1].created_at,
          details: [
            `Re-analyzed with ${queries.length} query results`,
            'Using thinking_level="high" for deep reasoning',
            geminiResponse.summary || 'Comprehensive analysis complete'
          ]
        })
      }
    }

    // Task 6: Threats Identified
    if (geminiResponse && geminiResponse.threats_identified && geminiResponse.threats_identified.length > 0) {
      geminiResponse.threats_identified.forEach((threat, index) => {
        tasks.push({
          id: `threat_${index}`,
          title: `Threat Detected: ${threat.threat_type}`,
          status: 'alert',
          timestamp: summary.interval_end,
          details: [
            `Process: ${threat.process_name} (PID: ${threat.pid})`,
            `Confidence: ${(threat.confidence * 100).toFixed(0)}%`,
            `Action: ${threat.recommended_action}`,
            ...(threat.evidence || [])
          ]
        })
      })
    }

    // Task 7: Final Verdict
    if (geminiResponse) {
      const riskLevel = geminiResponse.risk_score > 0.7 ? 'HIGH RISK' :
                       geminiResponse.risk_score > 0.4 ? 'MEDIUM RISK' : 'LOW RISK'
      tasks.push({
        id: 'verdict',
        title: `Final Verdict: ${riskLevel}`,
        status: geminiResponse.risk_score > 0.7 ? 'alert' : 'completed',
        timestamp: summary.interval_end,
        details: [
          `Overall Risk: ${(geminiResponse.risk_score * 100).toFixed(0)}%`,
          `Classification: ${geminiResponse.classification || 'N/A'}`,
          geminiResponse.reasoning || 'Investigation complete'
        ]
      })
    }

    return tasks
  }

  const tasks = buildInvestigationTasks()

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#10b981" strokeWidth="2">
            <polyline points="20 6 9 17 4 12"/>
          </svg>
        )
      case 'active':
        return (
          <div style={{
            width: '16px',
            height: '16px',
            border: '2px solid #3b82f6',
            borderTopColor: 'transparent',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }} />
        )
      case 'alert':
        return (
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#ef4444" strokeWidth="2">
            <path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/>
            <line x1="12" y1="9" x2="12" y2="13"/>
            <line x1="12" y1="17" x2="12.01" y2="17"/>
          </svg>
        )
      default:
        return (
          <div style={{
            width: '16px',
            height: '16px',
            border: '2px solid #6b7280',
            borderRadius: '50%'
          }} />
        )
    }
  }

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed': return '#10b981'
      case 'active': return '#3b82f6'
      case 'alert': return '#ef4444'
      default: return '#6b7280'
    }
  }

  return (
    <div style={{
      background: '#1a1a1a',
      border: '1px solid #2a2a2a',
      borderRadius: '12px',
      height: 'fit-content',
      maxHeight: 'calc(100vh - 200px)',
      display: 'flex',
      flexDirection: 'column',
      position: 'sticky',
      top: '20px'
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
            Live Investigation
          </h3>
          <p style={{ fontSize: '12px', color: '#9ca3af' }}>
            {new Date(summary.interval_start).toLocaleTimeString()} - 
            {new Date(summary.interval_end).toLocaleTimeString()}
          </p>
        </div>
        <button
          onClick={onClose}
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

      {/* Timeline */}
      <div style={{
        flex: 1,
        overflowY: 'auto',
        padding: '20px'
      }}>
        <div style={{ position: 'relative' }}>
          {/* Vertical line */}
          <div style={{
            position: 'absolute',
            left: '7px',
            top: '0',
            bottom: '0',
            width: '2px',
            background: '#2a2a2a'
          }} />

          {/* Tasks */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            {tasks.map((task) => {
              const isExpanded = expandedTask === task.id
              const isActive = task.status === 'active'

              return (
                <div key={task.id} style={{ position: 'relative', paddingLeft: '32px' }}>
                  {/* Icon */}
                  <div style={{
                    position: 'absolute',
                    left: '0',
                    top: '2px',
                    zIndex: 1
                  }}>
                    {getStatusIcon(task.status)}
                  </div>

                  {/* Task Card */}
                  <div
                    onClick={() => setExpandedTask(isExpanded ? null : task.id)}
                    style={{
                      background: '#0a0a0a',
                      border: `1px solid ${isActive ? getStatusColor(task.status) : '#2a2a2a'}`,
                      borderRadius: '8px',
                      padding: '12px',
                      cursor: 'pointer',
                      transition: 'all 0.2s',
                      animation: isActive ? 'borderPulse 2s infinite' : 'none'
                    }}
                  >
                    {/* Title */}
                    <div style={{
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'space-between',
                      marginBottom: isExpanded ? '12px' : '0'
                    }}>
                      <div style={{
                        fontSize: '13px',
                        fontWeight: '600',
                        color: getStatusColor(task.status),
                        animation: isActive ? 'textBlink 2s infinite' : 'none'
                      }}>
                        {task.title}
                      </div>
                      <svg
                        width="16"
                        height="16"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="#6b7280"
                        strokeWidth="2"
                        style={{
                          transform: isExpanded ? 'rotate(180deg)' : 'rotate(0deg)',
                          transition: 'transform 0.2s'
                        }}
                      >
                        <polyline points="6 9 12 15 18 9"/>
                      </svg>
                    </div>

                    {/* Timestamp */}
                    {!isExpanded && (
                      <div style={{ fontSize: '11px', color: '#6b7280' }}>
                        {new Date(task.timestamp).toLocaleTimeString()}
                      </div>
                    )}

                    {/* Details (Expanded) */}
                    {isExpanded && (
                      <div style={{
                        fontSize: '12px',
                        color: '#9ca3af',
                        paddingTop: '8px',
                        borderTop: '1px solid #2a2a2a'
                      }}>
                        <div style={{ marginBottom: '8px', color: '#6b7280', fontSize: '11px' }}>
                          {new Date(task.timestamp).toLocaleString()}
                        </div>
                        {task.details.map((detail, i) => (
                          <div key={i} style={{
                            marginBottom: '6px',
                            paddingLeft: '12px',
                            position: 'relative'
                          }}>
                            <span style={{
                              position: 'absolute',
                              left: '0',
                              color: '#6b7280'
                            }}>•</span>
                            {detail}
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Footer Stats */}
      <div style={{
        padding: '16px 20px',
        borderTop: '1px solid #2a2a2a',
        background: '#0a0a0a',
        borderRadius: '0 0 12px 12px'
      }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '12px', fontSize: '11px' }}>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#10b981', fontWeight: '700', fontSize: '16px' }}>
              {tasks.filter(t => t.status === 'completed').length}
            </div>
            <div style={{ color: '#6b7280' }}>Completed</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#3b82f6', fontWeight: '700', fontSize: '16px' }}>
              {tasks.filter(t => t.status === 'active').length}
            </div>
            <div style={{ color: '#6b7280' }}>Active</div>
          </div>
          <div style={{ textAlign: 'center' }}>
            <div style={{ color: '#ef4444', fontWeight: '700', fontSize: '16px' }}>
              {tasks.filter(t => t.status === 'alert').length}
            </div>
            <div style={{ color: '#6b7280' }}>Alerts</div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default LiveInvestigationSidebar
