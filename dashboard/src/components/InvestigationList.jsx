import RiskMeter from './RiskMeter'

function InvestigationList({ investigations, loading, onSelect, selectedId }) {
  if (loading) {
    return (
      <div className="card">
        <p style={{ color: '#9ca3af', textAlign: 'center' }}>Loading investigations...</p>
      </div>
    )
  }

  if (investigations.length === 0) {
    return (
      <div className="card">
        <p style={{ color: '#9ca3af', textAlign: 'center' }}>No investigations yet</p>
        <p style={{ color: '#6b7280', fontSize: '13px', textAlign: 'center', marginTop: '8px' }}>
          Waiting for suspicious processes...
        </p>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>
        Active Investigations ({investigations.filter(i => i.is_active).length})
      </h2>

      <table>
        <thead>
          <tr>
            <th>Process</th>
            <th>PID</th>
            <th>Status</th>
            <th>Risk</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {investigations.map(inv => (
            <tr
              key={inv.id}
              onClick={() => onSelect(inv)}
              style={{
                cursor: 'pointer',
                background: selectedId === inv.id ? '#1a1a2a' : 'transparent'
              }}
            >
              <td>
                <div style={{ fontWeight: '500' }}>{inv.process_name}</div>
                <div style={{ fontSize: '12px', color: '#6b7280' }}>
                  {inv.process_path || 'Unknown path'}
                </div>
              </td>
              <td style={{ color: '#9ca3af' }}>{inv.pid}</td>
              <td>
                <span className={`status-badge status-${inv.status.toLowerCase()}`}>
                  {inv.current_phase}
                </span>
              </td>
              <td>
                <div style={{ width: '120px' }}>
                  <RiskMeter score={inv.risk_score} level={inv.risk_level} compact />
                </div>
              </td>
              <td style={{ color: '#9ca3af', fontSize: '13px' }}>
                {new Date(inv.triggered_at).toLocaleTimeString()}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

export default InvestigationList
