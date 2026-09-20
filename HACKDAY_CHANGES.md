# HackDay Edition Changes

## Product direction
SentinelX (built on PROCSee) is presented as an AI-assisted endpoint defense command center:
**Detect → Investigate → Explain → Decide → Respond → Audit**

## New frontend
- New responsive command-center shell
- Animated telemetry visuals
- Attack-chain reconstruction panel
- Risk/defense metrics
- Human approval gate
- What-if response simulation
- Live event stream

## Backend compatibility
The redesign consumes the existing investigations API and WebSocket stream. Existing investigation, evidence, report, analytics and configuration pages are retained.

## Safety
Containment buttons in the new command center are explicitly demo/simulation actions. No destructive endpoint action was added to the frontend-only hackathon patch.


## Live AI upgrade

- Added a server-side AI gateway at `api/ai.py`.
- Added Gemini 2.5 Flash as the primary live analyst.
- Added Groq GPT-OSS 20B as a secondary live analyst.
- Added automatic provider fallback and deterministic local safety net.
- Added one-call-per-analyst-action behavior to reduce free-tier quota usage.
- API keys remain server-side.
- Added live/local provider status to the Command Center.
- Added restrained entrance, reveal, status, hover, and reduced-motion animations.

- Live Windows monitoring is now opt-in (`ENABLE_LIVE_MONITORING=true`) so an API key alone cannot start continuous background analysis and consume free-tier quota.
- `AUTO_INVESTIGATE` defaults to false for the hackathon demo.
