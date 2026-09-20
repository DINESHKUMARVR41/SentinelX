# SentinelX — AI-Powered Autonomous Endpoint Defense & Incident Response

*AI-Powered Endpoint Defense* · **Hackathon prototype · demonstration environment**

> SentinelX is an **AI-assisted endpoint investigation** prototype with **human-approved response**. It is not a production EDR product. All response actions in the demo are **simulated** and never modify a real machine.

## Problem
Analysts drown in isolated endpoint alerts. Weak signals (an Office app spawning PowerShell, an encoded command, a new outbound connection) are hard to connect quickly, and automated responses without human oversight are risky.

## Solution
SentinelX correlates process, command-line and network signals into one incident, explains *why* it looks suspicious using concise evidence, and gates every response behind analyst approval, with a full audit trail.

**Lifecycle:** Detect → Investigate → Explain → Decide → Respond → Audit

## Key Features
- One-click **Run Attack Simulation** (deterministic, works offline, no API key)
- Interactive attack-chain graph (process, PID, parent PID, command, timestamp, risk)
- Evidence-based explanation (no hidden reasoning exposed)
- Human approval gate: Investigate / Approve Containment / Reject / Simulate Isolation / Generate Incident Report
- What-if resilience simulation: primary containment fails → fallback → verification
- Audit trail (local + optionally synced to backend over REST/WebSocket)
- Retained from PROCSee: live Windows monitoring, Gemini-powered investigations, incidents, analytics, configuration pages

## Architecture
```
React dashboard (Vite) ──REST/WS──> FastAPI ──> Agent (WMI/psutil monitor, Gemini) ──> SQLite
        │                              └─ /api/demo/audit (simulation audit trail)
        └─ demo/scenario.js + useDemoEngine.js  (local deterministic simulation; works with backend down)
```

## Technology Stack
React 18, Vite, Recharts, lucide-react · Python 3.10+, FastAPI, aiosqlite, psutil, google-genai (optional live AI)

## Demo Mode
Demo mode is automatic. The dashboard always has a local engine, so the workflow runs even if the backend, internet, Gemini key or WebSocket are unavailable (the header chip shows `OFFLINE · LOCAL DEMO ENGINE`).

3–5 minute script: **Run Attack Simulation** → click chain nodes → **Investigate** → read explanation → **Run what-if** → **Approve Containment** → **Simulate Isolation** → **Generate Incident Report** → show Audit trail.

All scenario data (host `WKSTN-FIN-07`, PIDs, `203.0.113.50` documentation IP) is fabricated and labelled as simulation.

## Installation
```bash
pip install -r requirements.txt        # pywin32/WMI install only on Windows
cd dashboard && npm install
cp .env.example .env                    # optional
```

## Running Backend
```bash
python -m api.main        # http://localhost:8000
```
Without `GEMINI_API_KEY` the backend starts in demo mode (live monitoring/AI disabled).

## Running Frontend
```bash
cd dashboard && npm run dev    # http://localhost:5173 (proxies /api and /ws to :8000)
npm run build                  # production build check
```

## Environment Variables
| Variable | Purpose |
|---|---|
| `GEMINI_API_KEY` | Optional. Enables live Gemini investigation and Windows process monitoring |
| `GEMINI_MODEL_PRO` | Model name (default `gemini-3-pro-preview`) |
| `DATABASE_PATH`, `EVIDENCE_STORAGE_PATH` | Storage locations |
| `AUTO_INVESTIGATE`, `INVESTIGATION_DEPTH`, `MAX_CONCURRENT_INVESTIGATIONS`, `LOG_RETENTION_HOURS` | Agent behaviour |
| `ENABLE_BETA_PREVENTION` | Inherited beta flag; keep `false` |

## Project Structure
```
agent/        monitoring, investigation orchestration, Gemini client (inherited from PROCSee)
api/          FastAPI app, investigations/config routes, demo.py (simulation audit), websocket
dashboard/    React UI; src/demo/ = SentinelX simulation engine; components/CommandCenter.jsx
database/     SQLite schema
demo/         original PowerShell demo scripts
```

## Security / Simulation Disclaimer
Prototype for demonstration. Containment, isolation and reports in the demo are simulated. SentinelX does not guarantee threat detection or prevention, does not perform autonomous malware removal, and is not production-grade EDR. Live-mode analysis depends on an external AI service and can be wrong; a human should review every decision.

## Original Project Attribution
SentinelX is built on top of the open-source **PROCSee** project (MIT License, see `LICENSE`), whose monitoring, investigation agent, API and storage layers are retained. The original README is preserved in `PROCSEE_ORIGINAL_README.md`. Hackathon changes: SentinelX branding and command-center UI, deterministic simulation engine, attack-chain view, human approval gate, what-if resilience simulation, audit trail/report, key-less backend startup and connection hardening.

## Hackathon Innovation
Correlated attack-chain explanation + human-in-the-loop response + rehearsed fallback (what-if) + a fully offline deterministic demo path.

## Future Scope
Real EDR telemetry connectors (Sysmon/ETW), signed and reversible response actions with role-based approval, persisted audit storage, SIEM export, cross-endpoint correlation, evaluation on labelled attack datasets.


## Live AI providers (free-tier capable)

SentinelX supports two optional live providers for the analyst explanation step:

1. **Gemini 2.5 Flash** — primary provider by default.
2. **Groq GPT-OSS 20B** — automatic fallback when Gemini is unavailable.

The browser never receives either API key. The FastAPI AI gateway reads keys from `.env`.

Copy `.env.example` to `.env` and set:

```env
GEMINI_API_KEY=
GEMINI_MODEL_PRO=gemini-2.5-flash

GROQ_API_KEY=
GROQ_MODEL=openai/gpt-oss-20b

AI_PRIMARY_PROVIDER=gemini
AI_FALLBACK_ENABLED=true
```

The demo makes a single compact AI request only when the analyst clicks **Explain with Live AI**. If both providers are unavailable or rate-limited, SentinelX automatically uses its deterministic local analysis, so the demo does not fail.

API keys must never be committed to GitHub.

### Provider routing

```text
Analyst clicks Explain with Live AI
              |
              v
       Gemini 2.5 Flash
              |
        unavailable?
              v
        Groq GPT-OSS 20B
              |
        unavailable?
              v
   Deterministic local analysis
```

This is a prototype. Provider availability and free-tier quotas are controlled by the respective providers and can change.
