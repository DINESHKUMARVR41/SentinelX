import { useState, useEffect } from 'react'
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts'
import { Activity, Database, Cpu, TrendingUp, AlertTriangle, Clock } from 'lucide-react'

const COLORS = {
  LOW: '#4ade80',
  MEDIUM: '#fbbf24',
  HIGH: '#fb923c',
  CRITICAL: '#ef4444'
}

function SystemOverview({ investigations, onSelectInvestigation }) {
  const [systemMetrics, setSystemMetrics] = useState(null)
  const [activityTimeline, setActivityTimeline] = useState([])
  const [riskDistribution, setRiskDistribution] = useState([])
  const [topProcesses, setTopProcesses] = useState([])
  const [recentActivity, setRecentActivity] = useState([])

  // Calculate basic stats
  const activeCount = investigations.filter(i => i.is_active).length
  const completedCount = investigations.filter(i => !i.is_active).length
  const highRiskCount = investigations.filter(i => i.risk_level === 'HIGH' || i.risk_level === 'CRITICAL').length
  const avgRisk = investigations.length > 0
    ? investigations.reduce((sum, i) => sum + i.risk_score, 0) / investigations.length
    : 0

  // Fetch system metrics
  useEffect(() => {
    const fetchMetrics = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/investigations/stats/system-metrics')
        if (!response.ok) {
          console.log('System metrics endpoint not available yet')
          return
        }
        const data = await response.json()
        setSystemMetrics(data)
      } catch (error) {
        console.error('Failed to fetch system metrics:', error)
      }
    }

    fetchMetrics()
    const interval = setInterval(fetchMetrics, 5000) // Update every 5 seconds
    return () => clearInterval(interval)
  }, [])

  // Fetch activity timeline
  useEffect(() => {
    const fetchTimeline = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/investigations/stats/activity-timeline?hours=24')
        if (!response.ok) {
          console.log('Timeline endpoint not available yet')
          return
        }
        const data = await response.json()
        
        // Transform data for chart
        const hourMap = {}
        if (Array.isArray(data)) {
          data.forEach(item => {
            if (!hourMap[item.hour]) {
              hourMap[item.hour] = { hour: item.hour, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0 }
            }
            hourMap[item.hour][item.risk_level] = item.count
          })
        }
        
        setActivityTimeline(Object.values(hourMap))
      } catch (error) {
        console.error('Failed to fetch timeline:', error)
      }
    }

    fetchTimeline()
    const interval = setInterval(fetchTimeline, 30000) // Update every 30 seconds
    return () => clearInterval(interval)
  }, [])

  // Fetch risk distribution
  useEffect(() => {
    const fetchDistribution = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/investigations/stats/risk-distribution')
        if (!response.ok) {
          console.log('Risk distribution endpoint not available yet')
          return
        }
        const data = await response.json()
        setRiskDistribution(data)
      } catch (error) {
        console.error('Failed to fetch risk distribution:', error)
      }
    }

    fetchDistribution()
    const interval = setInterval(fetchDistribution, 30000)
    return () => clearInterval(interval)
  }, [])

  // Fetch top processes
  useEffect(() => {
    const fetchTopProcesses = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/investigations/stats/top-processes?limit=5')
        if (!response.ok) {
          console.log('Top processes endpoint not available yet')
          return
        }
        const data = await response.json()
        setTopProcesses(data)
      } catch (error) {
        console.error('Failed to fetch top processes:', error)
      }
    }

    fetchTopProcesses()
    const interval = setInterval(fetchTopProcesses, 30000)
    return () => clearInterval(interval)
  }, [])

  // Update recent activity
  useEffect(() => {
    setRecentActivity(investigations.slice(0, 8))
  }, [investigations])

  const handleActivityClick = (inv) => {
    if (onSelectInvestigation) {
      onSelectInvestigation(inv)
    }
  }

  return (
    <div style={{ padding: '20px' }}>
      {/* Stats Cards Row 1 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        <div className="card">
          <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '8px' }}>
            Active Investigations
          </div>
          <div style={{ fontSize: '32px', fontWeight: '600', color: '#0066cc' }}>
            {activeCount}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '8px' }}>
            Completed
          </div>
          <div style={{ fontSize: '32px', fontWeight: '600', color: '#4ade80' }}>
            {completedCount}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '8px' }}>
            High Risk Threats
          </div>
          <div style={{ fontSize: '32px', fontWeight: '600', color: '#ef4444' }}>
            {highRiskCount}
          </div>
        </div>

        <div className="card">
          <div style={{ fontSize: '13px', color: '#9ca3af', marginBottom: '8px' }}>
            Average Risk Score
          </div>
          <div style={{ fontSize: '32px', fontWeight: '600', color: '#fbbf24' }}>
            {avgRisk.toFixed(2)}
          </div>
        </div>
      </div>

      {/* System Health Row */}
      {systemMetrics && (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px', marginBottom: '20px' }}>
          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>CPU Usage</div>
              <Cpu size={18} color="#0066cc" />
            </div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#0066cc' }}>
              {systemMetrics.cpu_percent}%
            </div>
            <div style={{ 
              width: '100%', 
              height: '4px', 
              background: '#2a2a2a', 
              borderRadius: '2px', 
              marginTop: '8px',
              overflow: 'hidden'
            }}>
              <div style={{ 
                width: `${systemMetrics.cpu_percent}%`, 
                height: '100%', 
                background: '#0066cc',
                transition: 'width 0.3s ease'
              }} />
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>Memory Usage</div>
              <Activity size={18} color="#10b981" />
            </div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#10b981' }}>
              {systemMetrics.memory_mb} MB
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
              SentinelX process
            </div>
          </div>

          <div className="card">
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '8px' }}>
              <div style={{ fontSize: '13px', color: '#9ca3af' }}>Database Size</div>
              <Database size={18} color="#f59e0b" />
            </div>
            <div style={{ fontSize: '28px', fontWeight: '600', color: '#f59e0b' }}>
              {(systemMetrics.database_size_mb || 0).toFixed(1)} MB
            </div>
            <div style={{ fontSize: '11px', color: '#6b7280', marginTop: '4px' }}>
              Including WAL files
            </div>
          </div>
        </div>
      )}

      {/* Charts Row */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '16px', marginBottom: '20px' }}>
        {/* Activity Timeline Chart */}
        <div className="card" style={{ minHeight: '300px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <TrendingUp size={18} />
            Suspicious Activity Timeline (24h)
          </h2>
          {activityTimeline.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={activityTimeline}>
                <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2a" />
                <XAxis 
                  dataKey="hour" 
                  stroke="#9ca3af"
                  fontSize={11}
                  tickFormatter={(value) => new Date(value).toLocaleTimeString([], { hour: '2-digit' })}
                />
                <YAxis stroke="#9ca3af" fontSize={11} />
                <Tooltip 
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '6px' }}
                  labelStyle={{ color: '#fff' }}
                />
                <Legend />
                <Bar dataKey="LOW" stackId="a" fill={COLORS.LOW} name="Low" />
                <Bar dataKey="MEDIUM" stackId="a" fill={COLORS.MEDIUM} name="Medium" />
                <Bar dataKey="HIGH" stackId="a" fill={COLORS.HIGH} name="High" />
                <Bar dataKey="CRITICAL" stackId="a" fill={COLORS.CRITICAL} name="Critical" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', color: '#6b7280' }}>
              No activity data yet
            </div>
          )}
        </div>

        {/* Risk Distribution Pie Chart */}
        <div className="card" style={{ minHeight: '300px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <AlertTriangle size={18} />
            Risk Level Distribution
          </h2>
          {riskDistribution.length > 0 ? (
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie
                  data={riskDistribution}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ risk_level, percent }) => `${risk_level} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="count"
                  nameKey="risk_level"
                >
                  {riskDistribution.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[entry.risk_level] || '#6b7280'} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ background: '#1a1a1a', border: '1px solid #2a2a2a', borderRadius: '6px' }}
                />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '250px', color: '#6b7280' }}>
              No distribution data yet
            </div>
          )}
        </div>
      </div>

      {/* Bottom Row: Recent Activity + Top Processes */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '16px' }}>
        {/* Recent Activity */}
        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Clock size={18} />
            Recent Activity
          </h2>

          {recentActivity.length === 0 ? (
            <p style={{ color: '#9ca3af', textAlign: 'center', padding: '20px' }}>No recent activity</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {recentActivity.map(inv => (
                <div
                  key={inv.id}
                  onClick={() => handleActivityClick(inv)}
                  style={{
                    background: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                    borderRadius: '6px',
                    padding: '12px',
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.background = '#1a1a1a'
                    e.currentTarget.style.borderColor = '#3a3a3a'
                    e.currentTarget.style.transform = 'translateX(4px)'
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.background = '#0a0a0a'
                    e.currentTarget.style.borderColor = '#2a2a2a'
                    e.currentTarget.style.transform = 'translateX(0)'
                  }}
                >
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '14px', fontWeight: '500', marginBottom: '4px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      {inv.process_name}
                      <span style={{ fontSize: '12px', color: '#6b7280' }}>PID {inv.pid}</span>
                    </div>
                    <div style={{ fontSize: '11px', color: '#9ca3af' }}>
                      {new Date(inv.triggered_at).toLocaleString()}
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                    {inv.is_active && (
                      <span style={{ 
                        fontSize: '10px', 
                        padding: '2px 8px', 
                        background: '#1e3a8a', 
                        color: '#93c5fd',
                        borderRadius: '4px',
                        fontWeight: '500'
                      }}>
                        LIVE
                      </span>
                    )}
                    <span className={`badge badge-${inv.risk_level.toLowerCase()}`}>
                      {inv.risk_level}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Top Processes */}
        <div className="card">
          <h2 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Activity size={18} />
            Top Suspicious Processes
          </h2>

          {topProcesses.length === 0 ? (
            <p style={{ color: '#9ca3af', textAlign: 'center', padding: '20px', fontSize: '13px' }}>
              No data yet
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {topProcesses.map((proc, index) => (
                <div
                  key={index}
                  style={{
                    background: '#0a0a0a',
                    border: '1px solid #2a2a2a',
                    borderRadius: '6px',
                    padding: '10px'
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                    <div style={{ fontSize: '13px', fontWeight: '500' }}>
                      {proc.process_name}
                    </div>
                    <span className={`badge badge-${proc.max_risk_level.toLowerCase()}`} style={{ fontSize: '10px' }}>
                      {proc.max_risk_level}
                    </span>
                  </div>
                  <div style={{ fontSize: '11px', color: '#6b7280' }}>
                    {proc.investigation_count} investigations • Avg risk: {proc.avg_risk_score.toFixed(2)}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default SystemOverview
