import { useState } from 'react'

function EvidenceTimeline({ evidence }) {
  const [expandedId, setExpandedId] = useState(null)

  const getImportanceColor = (importance) => {
    switch (importance) {
      case 'CRITICAL': return '#ef4444'
      case 'RELEVANT': return '#fbbf24'
      case 'INCIDENTAL': return '#9ca3af'
      default: return '#9ca3af'
    }
  }

  const formatContent = (content) => {
    try {
      const parsed = JSON.parse(content)
      return JSON.stringify(parsed, null, 2)
    } catch {
      return content
    }
  }

  if (evidence.length === 0) {
    return (
      <p style={{ color: '#9ca3af', textAlign: 'center' }}>No evidence collected yet</p>
    )
  }

  return (
    <div>
      {evidence.map((item, index) => (
        <div
          key={item.id}
          style={{
            borderLeft: `2px solid ${getImportanceColor(item.importance)}`,
            paddingLeft: '16px',
            marginBottom: '16px',
            paddingBottom: index === evidence.length - 1 ? '0' : '16px'
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '8px' }}>
            <div>
              <div style={{ fontSize: '13px', fontWeight: '500', marginBottom: '4px' }}>
                {item.evidence_type.replace(/_/g, ' ')}
              </div>
              <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                {new Date(item.collected_at).toLocaleTimeString()}
              </div>
            </div>
            <span
              style={{
                fontSize: '11px',
                color: getImportanceColor(item.importance),
                fontWeight: '500'
              }}
            >
              {item.importance}
            </span>
          </div>

          <div
            onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
            style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              borderRadius: '4px',
              padding: '12px',
              cursor: 'pointer',
              fontSize: '12px',
              fontFamily: 'monospace',
              maxHeight: expandedId === item.id ? 'none' : '60px',
              overflow: 'hidden',
              position: 'relative'
            }}
          >
            <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
              {formatContent(item.content)}
            </pre>
            {expandedId !== item.id && (
              <div style={{
                position: 'absolute',
                bottom: 0,
                left: 0,
                right: 0,
                height: '30px',
                background: 'linear-gradient(transparent, #0a0a0a)',
                display: 'flex',
                alignItems: 'flex-end',
                justifyContent: 'center',
                fontSize: '11px',
                color: '#9ca3af'
              }}>
                Click to expand
              </div>
            )}
          </div>
        </div>
      ))}
    </div>
  )
}

export default EvidenceTimeline
