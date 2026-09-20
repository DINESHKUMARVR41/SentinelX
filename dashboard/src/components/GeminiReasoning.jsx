function GeminiReasoning({ analysis }) {
  if (!analysis || !analysis.analysis) {
    return (
      <p style={{ color: '#9ca3af', textAlign: 'center' }}>
        Analysis not yet available
      </p>
    )
  }

  const data = analysis.analysis

  return (
    <div>
      {/* Risk Assessment */}
      {data.risk_assessment && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Risk Assessment
          </h3>
          <div style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: '6px', padding: '12px' }}>
            <div style={{ marginBottom: '8px' }}>
              <span style={{ fontSize: '12px', color: '#9ca3af' }}>Classification: </span>
              <span style={{ fontSize: '13px', color: '#e0e0e0', fontWeight: '500' }}>
                {data.risk_assessment.classification}
              </span>
            </div>
            {data.risk_assessment.mitre_techniques && data.risk_assessment.mitre_techniques.length > 0 && (
              <div>
                <span style={{ fontSize: '12px', color: '#9ca3af' }}>MITRE Techniques: </span>
                <div style={{ display: 'flex', gap: '6px', marginTop: '6px', flexWrap: 'wrap' }}>
                  {data.risk_assessment.mitre_techniques.map(tech => (
                    <span
                      key={tech}
                      style={{
                        background: '#1a1a2a',
                        color: '#818cf8',
                        padding: '4px 8px',
                        borderRadius: '4px',
                        fontSize: '11px',
                        fontFamily: 'monospace'
                      }}
                    >
                      {tech}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Attack Chain */}
      {data.attack_chain && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Attack Chain
          </h3>
          <div style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: '6px', padding: '12px' }}>
            {Object.entries(data.attack_chain).map(([key, value]) => (
              <div key={key} style={{ marginBottom: '12px' }}>
                <div style={{ fontSize: '11px', color: '#9ca3af', textTransform: 'uppercase', marginBottom: '4px' }}>
                  {key.replace(/_/g, ' ')}
                </div>
                <div style={{ fontSize: '13px', color: '#e0e0e0' }}>
                  {Array.isArray(value) ? (
                    <ul style={{ margin: '4px 0', paddingLeft: '20px' }}>
                      {value.map((item, i) => (
                        <li key={i} style={{ marginBottom: '4px' }}>{item}</li>
                      ))}
                    </ul>
                  ) : (
                    value
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Uncertainties */}
      {data.uncertainties && data.uncertainties.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Uncertainties
          </h3>
          <div style={{ background: '#1a1a0a', border: '1px solid #2a2a1a', borderRadius: '6px', padding: '12px' }}>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {data.uncertainties.map((item, i) => (
                <li key={i} style={{ fontSize: '13px', color: '#fbbf24', marginBottom: '6px' }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* Recommended Next Steps */}
      {data.recommended_next_steps && data.recommended_next_steps.length > 0 && (
        <div style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Recommended Next Steps
          </h3>
          <div style={{ background: '#0a1a1a', border: '1px solid #1a2a2a', borderRadius: '6px', padding: '12px' }}>
            <ul style={{ margin: 0, paddingLeft: '20px' }}>
              {data.recommended_next_steps.map((item, i) => (
                <li key={i} style={{ fontSize: '13px', color: '#34d399', marginBottom: '6px' }}>
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}

      {/* False Positive Check */}
      {data.false_positive_check && (
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            False Positive Assessment
          </h3>
          <div style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: '6px', padding: '12px' }}>
            <p style={{ fontSize: '13px', color: '#e0e0e0', margin: 0 }}>
              {data.false_positive_check}
            </p>
          </div>
        </div>
      )}

      {/* Reasoning (if available) */}
      {data.reasoning && (
        <div style={{ marginTop: '24px' }}>
          <h3 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '12px', color: '#e0e0e0' }}>
            Reasoning
          </h3>
          <div style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', borderRadius: '6px', padding: '12px' }}>
            <p style={{ fontSize: '13px', color: '#9ca3af', margin: 0, lineHeight: '1.6' }}>
              {data.reasoning}
            </p>
          </div>
        </div>
      )}
    </div>
  )
}

export default GeminiReasoning
