function RiskMeter({ score, level, confidence, compact = false }) {
  const getRiskColor = (level) => {
    switch (level?.toUpperCase()) {
      case 'CRITICAL': return 'risk-critical'
      case 'HIGH': return 'risk-high'
      case 'MEDIUM': return 'risk-medium'
      case 'LOW': return 'risk-low'
      default: return 'risk-medium'
    }
  }

  const percentage = Math.round(score * 100)

  if (compact) {
    return (
      <div>
        <div className="risk-meter">
          <div
            className={`risk-meter-fill ${getRiskColor(level)}`}
            style={{ width: `${percentage}%` }}
          />
        </div>
        <div style={{ fontSize: '11px', color: '#9ca3af', marginTop: '4px' }}>
          {percentage}% • {level}
        </div>
      </div>
    )
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
        <span style={{ fontSize: '13px', color: '#9ca3af' }}>Risk Score</span>
        <span className={`badge badge-${level?.toLowerCase()}`}>
          {level}
        </span>
      </div>

      <div className="risk-meter" style={{ height: '12px' }}>
        <div
          className={`risk-meter-fill ${getRiskColor(level)}`}
          style={{ width: `${percentage}%` }}
        />
      </div>

      <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '8px' }}>
        <span style={{ fontSize: '13px', color: '#9ca3af' }}>
          Score: {score.toFixed(2)}
        </span>
        {confidence !== undefined && (
          <span style={{ fontSize: '13px', color: '#9ca3af' }}>
            Confidence: {(confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
    </div>
  )
}

export default RiskMeter
