import { useEffect, useState } from 'react'
import {
  Activity, AlertTriangle, Bot, CheckCircle2, ChevronRight, CircleDot, Crosshair, FileSearch, FileText,
  GitBranch, LockKeyhole, Network, Play, RotateCcw, ShieldAlert, ShieldCheck, Siren, Terminal, Timer, XCircle, Zap, Server
} from 'lucide-react'
import { useDemoEngine } from '../demo/useDemoEngine'
import { STAGES, INCIDENT, CHAIN, TELEMETRY, INDICATORS, INVESTIGATION_STEPS, EXPLANATION, RESPONSE_PLAN, ISOLATION_STEPS, WHATIF_STEPS } from '../demo/scenario'

const STAGE_ICONS = [ShieldAlert, FileSearch, Bot, Crosshair, LockKeyhole, Timer]

function RiskPill({ level = 'LOW' }) {
  return <span className={`risk-pill ${level.toLowerCase()}`}>{level}</span>
}

function CommandCenter({ investigations = [], connected = false }) {
  const { s, backend, run, reset, investigate, explainWithAI, approve, reject, isolate, runWhatIf, generateReport } = useDemoEngine()
  const [selected, setSelected] = useState(null)
  const [aiStatus, setAiStatus] = useState(null)

  useEffect(() => {
    fetch('/api/ai/status')
      .then(r => r.ok ? r.json() : null)
      .then(data => setAiStatus(data))
      .catch(() => setAiStatus(null))
  }, [])

  const started = s.stage >= 0
  const detected = s.stage >= 1
  const threatScore = [0, 18, 55, 71, 86, 96][s.shown] ?? 0
  const level = !started ? 'IDLE' : threatScore >= 80 ? 'CRITICAL' : threatScore >= 50 ? 'HIGH' : 'ELEVATED'
  const live = investigations.filter(i => i.is_active)
  const indicators = INDICATORS.filter(i => s.shown > CHAIN.findIndex(n => n.t === i.n) && CHAIN.findIndex(n => n.t === i.n) >= 0)
  const telemetry = TELEMETRY.slice(0, s.shown).reverse()
  const liveRows = investigations.slice(0, 3).map(i => ({
    ts: new Date(i.triggered_at || Date.now()).toLocaleTimeString([], { hour12: false }),
    event: `[LIVE] ${i.process_name || 'process'} triggered investigation`, level: (i.risk_level || 'MEDIUM').toUpperCase()
  }))
  const statusText = s.decision === 'rejected' ? 'Response rejected - monitoring continues'
    : s.responding ? 'Executing simulation…'
    : s.decision === 'approved' ? 'Containment simulated'
    : s.stage === 3 ? 'Awaiting analyst decision'
    : 'No incident awaiting decision'

  return (
    <div className="command-center">
      <section className="hero-panel">
        <div className="hero-copy">
          <div className="eyebrow"><span className="pulse-dot" /> AI-ASSISTED ENDPOINT INVESTIGATION · <span className="sim-tag">DEMO MODE · SIMULATED DATA</span></div>
          <h2>See the attack chain.<br /><span>Decide with evidence.</span></h2>
          <p>SentinelX correlates endpoint telemetry, explains why an incident looks suspicious, and keeps a human analyst in control of every response. Prototype running on a simulated incident; no real endpoint is affected.</p>
          <div className="hero-actions">
            <button className="neon-button" onClick={run} disabled={s.running || s.investigating}>
              <Play size={16} /> {started ? 'Re-run Attack Simulation' : 'Run Attack Simulation'}
            </button>
            {started && <button className="ghost-button" onClick={reset}><RotateCcw size={14} /> Reset</button>}
            <div className="connection-chip">
              <span className={connected || backend ? 'live-dot' : 'offline-dot'} />
              {connected ? 'BACKEND + WEBSOCKET' : backend ? 'BACKEND (POLLING)' : 'OFFLINE · LOCAL DEMO ENGINE'}
            </div>
            <div className="ai-status-chip">
              <Bot size={12} />
              {aiStatus?.gemini_configured ? 'GEMINI READY' : aiStatus?.groq_configured ? 'GROQ READY' : 'AI FALLBACK'}
            </div>
          </div>
        </div>
        <div className={`threat-orbit ${s.running ? 'active' : ''}`}>
          <div className="orbit-ring ring-one" />
          <div className="orbit-ring ring-two" />
          <div className="orbit-core">
            <ShieldAlert size={28} />
            <strong>{threatScore}</strong>
            <span>RISK</span>
          </div>
          <div className="orbit-tag tag-a">PROCESS</div>
          <div className="orbit-tag tag-b">NETWORK</div>
          <div className="orbit-tag tag-c">AI</div>
        </div>
      </section>

      <section className="metric-grid">
        <div className="metric-card"><div className="metric-icon red"><Siren size={18} /></div><div><span>Threat Level</span><strong>{level}</strong></div></div>
        <div className="metric-card"><div className="metric-icon amber"><AlertTriangle size={18} /></div><div><span>Active Incident</span><strong>{detected ? INCIDENT.id : started ? 'Detecting…' : 'None'}</strong></div></div>
        <div className="metric-card"><div className="metric-icon cyan"><Server size={18} /></div><div><span>Endpoint</span><strong className="small">{started ? 'WKSTN-FIN-07' : '—'}</strong></div></div>
        <div className="metric-card"><div className="metric-icon green"><Activity size={18} /></div><div><span>Indicators · Live cases</span><strong>{indicators.length} · {live.length}</strong></div></div>
      </section>

      <section className="workflow-strip" aria-label="SentinelX lifecycle">
        {STAGES.map((label, idx) => {
          const Icon = STAGE_ICONS[idx]
          const done = started && (idx < s.stage || (s.stage === 5 && idx === 5))
          const active = started && idx === s.stage && !done
          return (
            <div className={`workflow-step ${done ? 'done' : ''} ${active ? 'active' : ''}`} key={label}>
              <div className="workflow-number">{done ? '✓' : idx + 1}</div><Icon size={16} /><span>{label}</span>
              {idx < STAGES.length - 1 && <ChevronRight size={15} className="workflow-arrow" />}
            </div>
          )
        })}
      </section>

      <div className="dashboard-grid">
        <section className="glass-card attack-card">
          <div className="section-heading">
            <div><div className="section-kicker"><GitBranch size={14} /> 1 · DETECT — PROCESS CHAIN</div><h3>Attack-chain reconstruction</h3></div>
            <span className="live-badge"><CircleDot size={11} /> {started ? 'SIMULATED' : 'IDLE'}</span>
          </div>
          <p className="section-subtitle">{started ? INCIDENT.title : 'Click “Run Attack Simulation” to replay a simulated document-borne attack.'}</p>
          <div className="attack-chain">
            {s.shown === 0 && <div className="empty-state">No incident. Waiting for simulation.</div>}
            {CHAIN.slice(0, s.shown).map((node, idx) => (
              <div className="chain-node-wrap" key={node.id}>
                <button className={`chain-node ${selected === node.id ? 'selected' : ''}`} onClick={() => setSelected(selected === node.id ? null : node.id)}>
                  <div className={`chain-icon ${node.risk}`}><Terminal size={16} /></div>
                  <div className="chain-main"><strong>{node.name}</strong><span>{node.kind} · PID {node.pid} · PPID {node.ppid} · {node.ts}</span></div>
                  <RiskPill level={node.risk.toUpperCase()} />
                </button>
                {selected === node.id && (
                  <div className="node-detail">
                    <div><span>Process</span><b>{node.name}</b></div>
                    <div><span>PID / Parent PID</span><b>{node.pid} / {node.ppid}</b></div>
                    <div><span>Timestamp</span><b>{node.ts} (simulated)</b></div>
                    <div><span>Command</span><code>{node.cmd}</code></div>
                    <div><span>Why it matters</span><b>{node.note}</b></div>
                  </div>
                )}
                {idx < CHAIN.length - 1 && <div className="chain-link">{s.running && idx === s.shown - 1 && <span />}</div>}
              </div>
            ))}
          </div>

          {indicators.length > 0 && (
            <div className="indicator-list">
              <div className="mini-title">SUSPICIOUS INDICATORS</div>
              {indicators.map(i => <div key={i.id} className="indicator"><AlertTriangle size={12} /> {i.label}</div>)}
            </div>
          )}

          {detected && (
            <div className="investigation-box">
              <div className="mini-title">2 · INVESTIGATE</div>
              {s.stage === 1 && !s.investigating && <button className="neon-button" onClick={investigate}><FileSearch size={15} /> Investigate</button>}
              {INVESTIGATION_STEPS.slice(0, s.invStep).map((t, i) => <div className="inv-step" key={i}><CheckCircle2 size={12} /> {t}</div>)}
              {s.investigating && <div className="inv-step pending">Collecting evidence (simulated)…</div>}
            </div>
          )}

          {s.stage >= 2 && (
            <div className="explain-box">
              <div className="explain-icon"><Bot size={18} /></div>
              <div className="ai-explain-content">
                <div className="ai-explain-header">
                  <strong>3 · EXPLAIN</strong>
                  <span className={`ai-provider ${s.ai?.live ? 'live' : 'local'}`}>
                    {s.ai?.live ? `LIVE · ${s.ai.provider}` : 'LOCAL SAFETY NET'}
                  </span>
                </div>
                {!s.ai && (
                  <div className="ai-callout">
                    <div>
                      <b>Use live AI for this incident</b>
                      <span>One compact request. Gemini first, Groq fallback, local fallback if both are unavailable.</span>
                    </div>
                    <button className="neon-button compact" onClick={explainWithAI} disabled={s.aiLoading}>
                      <Bot size={14} /> {s.aiLoading ? 'Analyzing…' : 'Explain with Live AI'}
                    </button>
                  </div>
                )}
                {s.ai && (
                  <>
                    <strong>{s.ai.verdict} ({Math.round((s.ai.confidence || 0) * 100)}%)</strong>
                    <ul className="evidence-list">{(s.ai.evidence || EXPLANATION.evidence).map((e, i) => <li key={i}>{e}</li>)}</ul>
                    <p className="tech-line">{(s.ai.techniques || EXPLANATION.techniques).join(' · ')}</p>
                    <p className="tech-line">{s.ai.message || `Analysis provider: ${s.ai.provider}`}</p>
                  </>
                )}
              </div>
            </div>
          )}
        </section>

        <section className="glass-card response-card">
          <div className="section-heading">
            <div><div className="section-kicker"><LockKeyhole size={14} /> 4 · DECIDE · 5 · RESPOND</div><h3>Human-approved containment</h3></div>
            <span className="approval-badge">ANALYST GATE</span>
          </div>
          <div className="response-status">
            <div className={`status-orb ${s.responding ? 'approved' : s.decision === 'approved' ? 'completed' : ''}`}>{s.decision === 'rejected' ? <XCircle size={22} /> : <ShieldCheck size={22} />}</div>
            <div><strong>{statusText}</strong><span>SIMULATION: no action is executed on any real machine.</span></div>
          </div>
          <div className="action-list">
            {RESPONSE_PLAN.map((x, i) => (
              <div className="action-row" key={x}><div><span className="action-index">0{i + 1}</span>{x}</div><span className="action-safe">SIMULATED</span></div>
            ))}
          </div>
          <div className="button-grid">
            <button className="contain-button" onClick={approve} disabled={s.stage !== 3}><LockKeyhole size={14} /> Approve Containment</button>
            <button className="ghost-button wide" onClick={reject} disabled={s.stage !== 3}><XCircle size={14} /> Reject</button>
            <button className="ghost-button wide" onClick={isolate} disabled={s.decision !== 'approved' || s.responding || s.isolationStep > 0}><Network size={14} /> Simulate Isolation</button>
            <button className="ghost-button wide" onClick={generateReport} disabled={s.stage < 3}><FileText size={14} /> Generate Incident Report</button>
          </div>
          {s.isolationStep > 0 && <div className="iso-steps">{ISOLATION_STEPS.slice(0, s.isolationStep).map((t, i) => <div className="inv-step" key={i}><CheckCircle2 size={12} /> {t}</div>)}</div>}
          {s.report && <details className="report-preview"><summary>Incident report preview (downloaded as .md)</summary><pre>{s.report}</pre></details>}
          <div className="audit-line"><Timer size={13} /> Every step is recorded in the audit trail below.</div>
        </section>

        <section className="glass-card telemetry-card">
          <div className="section-heading"><div><div className="section-kicker"><Activity size={14} /> LIVE TELEMETRY (SIMULATED)</div><h3>Event stream</h3></div></div>
          <div className="telemetry-list">
            {telemetry.length + liveRows.length === 0 && <div className="empty-state">Endpoint telemetry stream idle.</div>}
            {[...telemetry, ...liveRows].map((e, idx) => <div className="telemetry-row" key={idx}><span className="telemetry-time">{e.ts}</span><span className={`telemetry-dot ${e.level.toLowerCase()}`} /><span>{e.event}</span><RiskPill level={e.level} /></div>)}
          </div>
        </section>

        <section className="glass-card simulation-card">
          <div className="section-heading"><div><div className="section-kicker"><Zap size={14} /> WHAT-IF ENGINE</div><h3>Resilience simulation</h3></div><span className="beta-badge">DETERMINISTIC</span></div>
          <p className="section-subtitle">What happens if primary containment fails? Fallback path is rehearsed before an analyst relies on it.</p>
          <div className={`scenario ${s.whatIfRunning ? 'running' : ''}`}>
            {WHATIF_STEPS.map((st, i) => {
              const shown = i < s.whatIfStep
              return (
                <div className={`whatif-step ${shown ? st.status : 'idle'}`} key={st.phase}>
                  <b>{shown ? (st.status === 'fail' ? '✕' : '✓') : i + 1}</b>
                  <div><strong>{st.phase}</strong><span>{st.text}</span></div>
                </div>
              )
            })}
          </div>
          <button className="ghost-button wide full" onClick={runWhatIf} disabled={!detected || s.whatIfRunning}><Zap size={14} /> {s.whatIfStep ? 'Re-run what-if' : 'Run what-if: primary containment fails'}</button>
          {!detected && <div className="audit-line">Available once an incident is detected.</div>}
        </section>

        <section className="glass-card audit-card">
          <div className="section-heading"><div><div className="section-kicker"><Timer size={14} /> 6 · AUDIT</div><h3>Audit trail</h3></div><span className="beta-badge">{backend ? 'SYNCED TO BACKEND' : 'LOCAL'}</span></div>
          <div className="audit-list">
            {s.audit.length === 0 && <div className="empty-state">No events recorded yet.</div>}
            {[...s.audit].reverse().slice(0, 30).map(a => (
              <div className="audit-row" key={a.id}><span className="telemetry-time">{a.time}</span><span className="audit-phase">{a.phase}</span><span>{a.action}{a.detail ? <em> — {a.detail}</em> : null}</span><span className="action-safe">{a.actor}</span></div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}

export default CommandCenter
