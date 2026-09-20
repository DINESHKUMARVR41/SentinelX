// SentinelX deterministic SIMULATION scenario. All data below is fabricated demo data.
// Nothing here is telemetry from a real machine.

export const STAGES = ['DETECT', 'INVESTIGATE', 'EXPLAIN', 'DECIDE', 'RESPOND', 'AUDIT']

export const INCIDENT = {
  id: 'SIM-0001',
  title: 'Office document spawned encoded PowerShell with outbound connection',
  endpoint: 'WKSTN-FIN-07 (simulated)',
  user: 'CORP\\j.doe (simulated)',
  baseTime: '10:42:11',
}

// t = seconds after simulation start at which the event is revealed
export const CHAIN = [
  { id: 'n1', t: 0, name: 'WINWORD.EXE', kind: 'Office application', pid: 4120, ppid: 3388, ts: '10:42:11',
    cmd: '"C:\\Program Files\\Microsoft Office\\root\\Office16\\WINWORD.EXE" "Invoice_Q3.docm"', risk: 'low',
    note: 'User opened a macro-enabled document.' },
  { id: 'n2', t: 2, name: 'powershell.exe', kind: 'Child process', pid: 5872, ppid: 4120, ts: '10:42:14',
    cmd: 'powershell.exe -NoProfile -WindowStyle Hidden -EncodedCommand <base64…>', risk: 'high',
    note: 'Office application spawned a hidden PowerShell process.' },
  { id: 'n3', t: 4, name: 'Encoded PowerShell', kind: 'Obfuscated command', pid: 5872, ppid: 4120, ts: '10:42:15',
    cmd: '-EncodedCommand JABjAGwAaQBlAG4AdAAgAD0A… (decodes to a download-and-run stub, simulated)', risk: 'critical',
    note: 'Base64-encoded command hides its intent from casual inspection.' },
  { id: 'n4', t: 6, name: 'Outbound Connection', kind: 'Network', pid: 5872, ppid: 4120, ts: '10:42:17',
    cmd: 'TCP 10.20.4.37:52144 -> 203.0.113.50:443 (documentation IP, simulated)', risk: 'high',
    note: 'First-seen external destination contacted by a scripting host.' },
  { id: 'n5', t: 8, name: 'payload.exe', kind: 'Payload execution', pid: 6640, ppid: 5872, ts: '10:42:21',
    cmd: 'C:\\Users\\Public\\payload.exe (unsigned, simulated)', risk: 'critical',
    note: 'Unsigned binary written to a public folder and launched by PowerShell.' },
]

export const TELEMETRY = [
  { t: 0, level: 'LOW', ts: '10:42:11', event: 'Process start: WINWORD.EXE (PID 4120) opened Invoice_Q3.docm' },
  { t: 1, level: 'MEDIUM', ts: '10:42:12', event: 'Macro execution observed in WINWORD.EXE' },
  { t: 2, level: 'HIGH', ts: '10:42:14', event: 'Process start: powershell.exe (PID 5872) parent WINWORD.EXE' },
  { t: 4, level: 'CRITICAL', ts: '10:42:15', event: 'PowerShell launched with -EncodedCommand and hidden window' },
  { t: 6, level: 'HIGH', ts: '10:42:17', event: 'Outbound TCP 443 to first-seen address 203.0.113.50' },
  { t: 8, level: 'CRITICAL', ts: '10:42:21', event: 'Unsigned payload.exe (PID 6640) started by powershell.exe' },
]

export const INDICATORS = [
  { id: 'i1', label: 'Office application spawned PowerShell', n: 2 },
  { id: 'i2', label: 'Encoded PowerShell command observed', n: 4 },
  { id: 'i3', label: 'Unusual parent-child process relationship', n: 2 },
  { id: 'i4', label: 'Suspicious outbound connection', n: 6 },
  { id: 'i5', label: 'Unsigned executable launched from public folder', n: 8 },
]

export const INVESTIGATION_STEPS = [
  'Collected process tree for PID 4120 and descendants',
  'Decoded EncodedCommand argument (simulated download-and-run stub)',
  'Checked destination 203.0.113.50 against first-seen network baseline',
  'Checked payload.exe signature: unsigned; path: C:\\Users\\Public',
  'Correlated 5 indicators across process, command line and network data',
]

export const EXPLANATION = {
  source: 'Deterministic demo analysis (no external AI call)',
  verdict: 'Likely malicious document-borne execution chain',
  confidence: 0.94,
  evidence: [
    'WINWORD.EXE spawned powershell.exe, which is uncommon for normal document use.',
    'PowerShell ran hidden with an encoded command, a common obfuscation pattern.',
    'The scripting host opened a connection to a first-seen external address.',
    'An unsigned binary was then launched from a public folder.',
    'Together, these indicators form one correlated chain that is higher risk than any single event.',
  ],
  techniques: ['T1204.002 User Execution: Malicious File', 'T1059.001 PowerShell', 'T1027 Obfuscated Files or Information', 'T1071 Application Layer Protocol'],
  note: 'Assessment is a prototype heuristic on simulated data, not a guarantee of detection.',
}

export const RESPONSE_PLAN = [
  'Suspend powershell.exe (PID 5872) and payload.exe (PID 6640)',
  'Block outbound traffic to 203.0.113.50',
  'Isolate endpoint from network, keep evidence collection channel',
  'Quarantine payload.exe and Invoice_Q3.docm for analysis',
]

export const ISOLATION_STEPS = [
  'Endpoint WKSTN-FIN-07 marked isolated (simulated)',
  'Network policy "quarantine-vlan" applied (simulated)',
  'Verification: no further outbound traffic from simulated endpoint',
]

// What-if: primary containment fails -> fallback -> verification
export const WHATIF_STEPS = [
  { phase: 'Primary response', text: 'Suspend powershell.exe and payload.exe', status: 'ok' },
  { phase: 'Failure injected', text: 'Process suspend denied (simulated insufficient privilege)', status: 'fail' },
  { phase: 'Fallback response', text: 'Network isolation + evidence capture (memory and process snapshot)', status: 'ok' },
  { phase: 'Verification', text: 'Outbound connections dropped; evidence preserved; escalate to analyst', status: 'ok' },
]

export function buildReport({ audit, decision }) {
  const lines = [
    `# SentinelX Incident Report (SIMULATION)`,
    ``,
    `> Simulation/demo data only. No real endpoint was inspected or modified.`,
    ``,
    `- **Incident:** ${INCIDENT.id} - ${INCIDENT.title}`,
    `- **Endpoint:** ${INCIDENT.endpoint}`,
    `- **User:** ${INCIDENT.user}`,
    `- **Verdict:** ${EXPLANATION.verdict} (confidence ${Math.round(EXPLANATION.confidence * 100)}%, prototype heuristic)`,
    `- **Analyst decision:** ${decision}`,
    ``,
    `## Attack chain`,
    ...CHAIN.map(n => `- ${n.ts} **${n.name}** (PID ${n.pid}, PPID ${n.ppid}) - ${n.note}`),
    ``,
    `## Evidence`,
    ...EXPLANATION.evidence.map(e => `- ${e}`),
    ``,
    `## Recommended response (simulated)`,
    ...RESPONSE_PLAN.map(r => `- ${r}`),
    ``,
    `## Audit trail`,
    ...audit.map(a => `- ${a.time} [${a.phase}] ${a.action}${a.detail ? ' - ' + a.detail : ''}`),
  ]
  return lines.join('\n')
}
