import { useState, useEffect } from 'react'
import InvestigationList from './components/InvestigationList'
import InvestigationDetail from './components/InvestigationDetail'
import ConfigPanel from './components/ConfigPanel'
import SystemOverview from './components/SystemOverview'
import AutonomousInvestigation from './components/AutonomousInvestigation'
import CommandCenter from './components/CommandCenter'
import { useWebSocket } from './hooks/useWebSocket'
import { fetchInvestigations } from './api/client'
import { Activity, LayoutDashboard, Shield, Settings, Search, Bell, Radar, Menu, X } from 'lucide-react'

function App() {
  const [investigations, setInvestigations] = useState([])
  const [selectedInv, setSelectedInv] = useState(null)
  const [activeTab, setActiveTab] = useState('command')
  const [loading, setLoading] = useState(true)
  const [mobileNav, setMobileNav] = useState(false)
  const { connected, lastMessage } = useWebSocket(`${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}/ws/investigations`)

  const loadInvestigations = async () => {
    try {
      const data = await fetchInvestigations()
      setInvestigations(data)
      setLoading(false)
    } catch (error) {
      console.error('Failed to load investigations:', error)
      setLoading(false)
    }
  }

  useEffect(() => {
    loadInvestigations()
    // Poll gently; skip while the tab is hidden. WebSocket events trigger extra refreshes.
    const interval = setInterval(() => { if (!document.hidden) loadInvestigations() }, 10000)
    return () => clearInterval(interval)
  }, [])

  useEffect(() => {
    if (lastMessage && ['new_investigation', 'investigation_update'].includes(lastMessage.type)) loadInvestigations()
  }, [lastMessage])

  const nav = [
    { id: 'command', label: 'Command Center', icon: LayoutDashboard },
    { id: 'autonomous', label: 'AI Investigator', icon: Radar },
    { id: 'investigations', label: 'Incidents', icon: Shield, count: investigations.filter(i => i.is_active).length },
    { id: 'overview', label: 'Analytics', icon: Activity },
    { id: 'config', label: 'System', icon: Settings }
  ]

  return (
    <div className="app-shell">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
        <div className="brand">
          <div className="brand-mark"><Shield size={20} /></div>
          <div><strong>Sentinel<span>X</span></strong><small>AI-POWERED ENDPOINT DEFENSE</small></div>
          <button className="mobile-close" onClick={() => setMobileNav(false)}><X size={18} /></button>
        </div>

        <div className="system-state">
          <span className={connected ? 'live-dot' : 'offline-dot'} />
          <div><strong>{connected ? 'BACKEND ONLINE' : 'DEMO / POLLING MODE'}</strong><small>Simulation-ready prototype</small></div>
        </div>

        <nav className="side-nav">
          <div className="nav-label">OPERATIONS</div>
          {nav.slice(0, 4).map(item => {
            const Icon = item.icon
            return <button key={item.id} className={activeTab === item.id ? 'nav-item active' : 'nav-item'} onClick={() => { setActiveTab(item.id); setMobileNav(false) }}><Icon size={17} /><span>{item.label}</span>{item.count > 0 && <b>{item.count}</b>}</button>
          })}
          <div className="nav-label system-label">PLATFORM</div>
          {nav.slice(4).map(item => { const Icon = item.icon; return <button key={item.id} className={activeTab === item.id ? 'nav-item active' : 'nav-item'} onClick={() => { setActiveTab(item.id); setMobileNav(false) }}><Icon size={17} /><span>{item.label}</span></button> })}
        </nav>

        <div className="sidebar-footer">
          <div className="agent-status"><div className="agent-avatar"><Radar size={15} /></div><div><strong>AI Investigator</strong><small>Human-approved response</small></div><span className="pulse-dot" /></div>
          <small>SentinelX prototype · built on PROCSee (MIT)</small>
        </div>
      </aside>

      <main className="main-area">
        <header className="topbar">
          <div className="topbar-left"><button className="mobile-menu" onClick={() => setMobileNav(true)}><Menu size={20} /></button><div className="crumb"><span>SECURITY OPERATIONS</span><b>/</b><strong>{nav.find(n => n.id === activeTab)?.label}</strong></div></div>
          <div className="topbar-actions">
            <div className="search-box"><Search size={15} /><span>Search investigations...</span></div>
            <button className="icon-button"><Bell size={17} /><i /></button>
          </div>
        </header>

        <div className="content-wrap">
          {activeTab === 'command' && <CommandCenter investigations={investigations} connected={connected} />}
          {activeTab === 'autonomous' && <AutonomousInvestigation />}
          {activeTab === 'investigations' && (
            <div className="page-stack">
              <div className="page-heading"><div><span className="section-kicker">CASE MANAGEMENT</span><h2>Security incidents</h2><p>Investigate, correlate and document suspicious endpoint behavior.</p></div></div>
              <div className="incident-layout">
                <InvestigationList investigations={investigations} loading={loading} onSelect={setSelectedInv} selectedId={selectedInv?.id} />
                {selectedInv && <InvestigationDetail investigation={selectedInv} onClose={() => setSelectedInv(null)} />}
              </div>
            </div>
          )}
          {activeTab === 'overview' && <div className="page-stack"><div className="page-heading"><div><span className="section-kicker">TELEMETRY</span><h2>Security analytics</h2><p>Operational trends from the endpoint investigation store.</p></div></div><SystemOverview investigations={investigations} onSelectInvestigation={(inv) => { setSelectedInv(inv); setActiveTab('investigations') }} /></div>}
          {activeTab === 'config' && <div className="page-stack"><div className="page-heading"><div><span className="section-kicker">PLATFORM</span><h2>System configuration</h2><p>Control monitoring and investigation behavior.</p></div></div><ConfigPanel /></div>}
        </div>
      </main>
    </div>
  )
}

export default App
