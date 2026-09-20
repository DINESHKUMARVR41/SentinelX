# HACKDAY_STATUS — SentinelX

## Phase 0 inspection and Phase 1–14 completion

**Stack:** React 18 + Vite 5 (`dashboard/`), FastAPI + uvicorn (`api/`), endpoint agent in `agent/`, SQLite, WebSocket `/ws/investigations`, optional Gemini/Groq live AI.

## Ready
- Command Center and responsive SentinelX branding.
- Deterministic offline demo that does not require Windows, Gemini, Groq or internet.
- Attack-chain reconstruction, evidence explanation, human approval gate, containment simulation, what-if resilience and audit/report workflow.
- Server-side AI gateway with Gemini 2.5 Flash primary, Groq GPT-OSS 20B fallback, and deterministic safety net.
- API keys remain server-side and are ignored by Git.
- Backend starts in degraded/demo mode without an API key.
- Windows-only monitoring dependencies are installed only on Windows.
- WebSocket and polling behavior hardened.
- Responsive animations include reduced-motion support.

## Live-mode limitation
- Real Windows monitoring and real provider calls depend on the user's Windows environment and valid API keys/free-tier availability. They were not exercised in the Linux build sandbox.

## Attribution
SentinelX is a modified hackathon prototype built on the open-source PROCSee project. The MIT license is retained and the original README is preserved as `PROCSEE_ORIGINAL_README.md`.
