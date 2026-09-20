[x] Inspection
[x] Existing errors fixed
[x] SentinelX rename
[x] Demo mode
[x] Attack chain
[x] AI explanation
[x] Human approval
[x] Containment simulation
[x] What-if resilience
[x] Offline fallback
[x] UI verification
[x] Frontend build
[x] Backend verification
[x] Final smoke test

## Errors found -> fixed
- Backend crash without GEMINI_API_KEY -> default empty, demo mode skips live monitors
- pywin32/WMI unconditional in requirements -> Windows-only markers (PyYAML added)
- Agent init failure killed API -> degraded mode, 503 on investigation routes
- WS URL hardcoded / gave up after 3 tries / no timer cleanup -> proxy-relative URL, capped backoff, cleanup
- 5s polling -> 10s, paused when tab hidden
- Static "simulation" toggle -> real state machine (scenario.js + useDemoEngine.js)
## Files changed
agent/{config,gemini_client,main}.py, api/{main,dependencies}.py, api/demo.py (new), requirements.txt, .env.example, README.md, PROCSEE_ORIGINAL_README.md (new), HACKDAY_*.md,
dashboard/{index.html,package.json}, src/{App.jsx,index.css}, src/hooks/useWebSocket.js, src/components/{CommandCenter,ConfigPanel,GeminiConversation,SystemOverview}.jsx, src/demo/{scenario.js,useDemoEngine.js}
## Verified (headless Chromium, key-less backend + vite dev)
Dashboard, nav (5 tabs), run sim, 5-node chain + node detail, investigate, explanation, what-if (4 steps), approve, isolation, report download, 28 audit rows, all 6 stages done.
## Remaining
- Live mode (Gemini + Windows WMI) untested here (Linux sandbox, no key).
- Google Fonts load from CDN; offline falls back to system fonts (only console error observed: blocked font request).
- Bundle is 776 kB (recharts); acceptable, not code-split.
- Real Investigations/Analytics pages show empty data until live mode is used.

## Post-demo live AI upgrade
- [x] Gemini 2.5 Flash live analyst gateway
- [x] Groq GPT-OSS 20B fallback gateway
- [x] Per-demo-run AI response caching to protect free-tier quota
- [x] Explicit live-monitoring opt-in to prevent background quota consumption
- [x] Live/local provider status in Command Center
- [x] UX motion polish and reduced-motion accessibility
