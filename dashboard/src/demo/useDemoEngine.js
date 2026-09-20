import { useCallback, useEffect, useRef, useState } from 'react'
import { CHAIN, TELEMETRY, INDICATORS, INVESTIGATION_STEPS, ISOLATION_STEPS, WHATIF_STEPS, buildReport } from './scenario'

const TICK = 800 // ms per scenario second
const INITIAL = {
  stage: -1,            // index into STAGES, -1 = idle
  running: false,       // detection stream in progress
  shown: 0,             // scenario events revealed (0..CHAIN.length)
  invStep: 0,           // investigation steps completed
  investigating: false,
  decision: null,       // null | 'approved' | 'rejected'
  responding: false,
  isolationStep: 0,
  whatIfStep: 0,
  whatIfRunning: false,
  report: null,
  audit: [],
  ai: null,
  aiLoading: false,
  runId: null,
}

const now = () => new Date().toLocaleTimeString([], { hour12: false })

export function useDemoEngine() {
  const [s, setS] = useState(INITIAL)
  const [backend, setBackend] = useState(null) // null unknown, true reachable, false offline
  const timers = useRef([])
  const seq = useRef(0)
  const sRef = useRef(s)
  sRef.current = s

  const later = useCallback((fn, ms) => { timers.current.push(setTimeout(fn, ms)) }, [])
  const clearTimers = useCallback(() => { timers.current.forEach(clearTimeout); timers.current = [] }, [])
  useEffect(() => clearTimers, [clearTimers])

  const log = useCallback((phase, action, detail = '', actor = 'system') => {
    const rec = { id: ++seq.current, time: now(), phase, action, detail, actor, simulated: true }
    setS(p => ({ ...p, audit: [...p.audit, rec].slice(-100) }))
    // Optional backend audit copy; the demo works fully without it.
    fetch('/api/demo/audit', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ phase, action, detail, actor })
    }).then(r => setBackend(r.ok)).catch(() => setBackend(false))
  }, [])

  const reset = useCallback(() => {
    clearTimers(); seq.current = 0; setS(INITIAL)
    fetch('/api/demo/audit', { method: 'DELETE' }).catch(() => {})
  }, [clearTimers])

  const run = useCallback(() => {
    clearTimers(); seq.current = 0
    setS({ ...INITIAL, stage: 0, running: true, runId: Date.now() })
    fetch('/api/demo/audit', { method: 'DELETE' }).catch(() => {})
    log('DETECT', 'Attack simulation started', 'Scenario SIM-0001: document-borne PowerShell chain (simulated)')
    CHAIN.forEach((n, i) => {
      later(() => {
        setS(p => ({ ...p, shown: i + 1 }))
        const ev = TELEMETRY[i]
        if (ev) log('DETECT', `Telemetry: ${n.name}`, ev.event)
      }, n.t * TICK + 400)
    })
    later(() => {
      setS(p => ({ ...p, running: false, stage: 1 }))
      log('DETECT', 'Incident SIM-0001 raised', '5 correlated indicators, risk CRITICAL - awaiting investigation')
    }, (CHAIN[CHAIN.length - 1].t + 1) * TICK + 400)
  }, [clearTimers, later, log])

  const investigate = useCallback(() => {
    setS(p => (p.stage === 1 && !p.investigating ? { ...p, investigating: true } : p))
    log('INVESTIGATE', 'Analyst started investigation', '', 'analyst')
    INVESTIGATION_STEPS.forEach((step, i) => later(() => {
      setS(p => ({ ...p, invStep: i + 1 }))
      log('INVESTIGATE', step)
    }, (i + 1) * 700))
    later(() => { setS(p => ({ ...p, stage: 2, investigating: false })); log('EXPLAIN', 'Evidence-based explanation generated', 'Deterministic demo analysis') }, (INVESTIGATION_STEPS.length + 1) * 700)
    later(() => { setS(p => ({ ...p, stage: 3 })); log('DECIDE', 'Awaiting analyst decision', 'Human approval required before any response') }, (INVESTIGATION_STEPS.length + 2) * 700 + 300)
  }, [later, log])

  const approve = useCallback(() => {
    setS(p => ({ ...p, decision: 'approved', stage: 4, responding: true }))
    log('RESPOND', 'Containment APPROVED (simulation)', 'Suspend processes, block connection, quarantine artifacts', 'analyst')
    later(() => {
      setS(p => ({ ...p, responding: false, stage: 5 }))
      log('RESPOND', 'Containment simulated', 'No real endpoint action was performed')
      log('AUDIT', 'Incident SIM-0001 recorded in audit trail')
    }, 1200)
  }, [later, log])

  const reject = useCallback(() => {
    setS(p => ({ ...p, decision: 'rejected', stage: 5 }))
    log('DECIDE', 'Containment REJECTED', 'Analyst chose to continue monitoring', 'analyst')
    log('AUDIT', 'Incident SIM-0001 recorded in audit trail')
  }, [log])

  const isolate = useCallback(() => {
    log('RESPOND', 'Simulate isolation requested', '', 'analyst')
    ISOLATION_STEPS.forEach((t, i) => later(() => { setS(p => ({ ...p, isolationStep: i + 1 })); log('RESPOND', t) }, (i + 1) * 700))
  }, [later, log])

  const runWhatIf = useCallback(() => {
    setS(p => ({ ...p, whatIfStep: 0, whatIfRunning: true }))
    log('DECIDE', 'What-if simulation started', 'Scenario: primary containment fails', 'analyst')
    WHATIF_STEPS.forEach((st, i) => later(() => {
      setS(p => ({ ...p, whatIfStep: i + 1, whatIfRunning: i + 1 < WHATIF_STEPS.length }))
      log('DECIDE', `What-if: ${st.phase}`, st.text)
    }, (i + 1) * 800))
  }, [later, log])

  const explainWithAI = useCallback(async () => {
    if (sRef.current.aiLoading) return
    setS(p => ({ ...p, aiLoading: true }))
    log('EXPLAIN', 'Live AI analysis requested', 'Gemini → Groq fallback → deterministic safety net', 'analyst')
    const payload = {
      incident: INCIDENT,
      attack_chain: CHAIN,
      indicators: INDICATORS,
      investigation_steps: INVESTIGATION_STEPS,
      telemetry: TELEMETRY,
      run_id: sRef.current.runId,
    }
    try {
      const response = await fetch('/api/ai/explain-demo', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })
      const data = await response.json()
      setS(p => ({ ...p, ai: data, aiLoading: false, stage: Math.max(p.stage, 3) }))
      log('EXPLAIN', 'AI explanation completed', `${data.provider || 'unknown'}${data.fallback_used ? ' (fallback)' : ''}`)
    } catch (error) {
      setS(p => ({ ...p, ai: {
        verdict: EXPLANATION.verdict,
        confidence: EXPLANATION.confidence,
        evidence: EXPLANATION.evidence,
        techniques: EXPLANATION.techniques,
        provider: 'deterministic-demo',
        live: false,
        message: 'AI gateway unavailable; local deterministic analysis kept the workflow running.',
      }, aiLoading: false, stage: Math.max(p.stage, 3) }))
      log('EXPLAIN', 'AI gateway unavailable; deterministic fallback used', String(error).slice(0, 120))
    }
  }, [log])

  const generateReport = useCallback(() => {
    const cur = sRef.current
    const text = buildReport({ audit: cur.audit, decision: cur.decision || 'pending' })
    try {
      const url = URL.createObjectURL(new Blob([text], { type: 'text/markdown' }))
      const a = document.createElement('a'); a.href = url; a.download = 'SentinelX-SIM-0001-report.md'; a.click()
      setTimeout(() => URL.revokeObjectURL(url), 1000)
    } catch { /* preview still shown */ }
    setS(p => ({ ...p, report: text }))
    log('AUDIT', 'Incident report generated (simulation)', 'SentinelX-SIM-0001-report.md', 'analyst')
  }, [log])

  return { s, backend, run, reset, investigate, explainWithAI, approve, reject, isolate, runWhatIf, generateReport }
}
