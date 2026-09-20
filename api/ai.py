"""
SentinelX live AI gateway.

Provider order:
1. Gemini 2.5 Flash (Google AI Studio free-tier capable)
2. Groq GPT-OSS 20B (free-tier capable, if available)
3. Deterministic local analysis

Only one live AI request is made for a demo incident when the analyst clicks
"Explain with Live AI". Keys are read from environment variables and never sent
to the browser.
"""
import json
import logging
import os
import re
from typing import Any, Dict

import httpx
from fastapi import APIRouter

from google import genai
from google.genai import types

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ai", tags=["ai"])

GEMINI_MODEL = os.getenv("GEMINI_MODEL", os.getenv("GEMINI_MODEL_PRO", "gemini-2.5-flash"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b")
PRIMARY = os.getenv("AI_PRIMARY_PROVIDER", "gemini").lower()
FALLBACK_ENABLED = os.getenv("AI_FALLBACK_ENABLED", "true").lower() in {"1", "true", "yes"}
_demo_cache: Dict[str, Dict[str, Any]] = {}

SCHEMA_HINT = {
    "verdict": "string",
    "confidence": "number between 0 and 1",
    "evidence": ["short evidence bullets"],
    "techniques": ["MITRE ATT&CK technique names or IDs when justified"],
}

SYSTEM_PROMPT = """You are SentinelX, an endpoint-security analyst.
Analyze only the supplied simulated telemetry. Do not invent facts.
Return concise, evidence-based output. Do not reveal hidden chain-of-thought.
Return JSON with exactly these fields:
verdict, confidence, evidence, techniques.
Confidence must be 0..1. Evidence must be a short list.
Mention that the evidence is simulated when appropriate.
"""

def _fallback() -> Dict[str, Any]:
    return {
        "verdict": "Likely malicious document-borne execution chain",
        "confidence": 0.94,
        "evidence": [
            "WINWORD.EXE spawned PowerShell, creating an unusual parent-child relationship.",
            "PowerShell used a hidden window and an encoded command.",
            "The scripting host contacted a first-seen external destination.",
            "An unsigned payload was launched from a public folder.",
            "The indicators form one correlated execution chain rather than isolated alerts.",
        ],
        "techniques": [
            "T1059.001 PowerShell",
            "T1027 Obfuscated Files or Information",
            "T1204.002 User Execution: Malicious File",
            "T1071 Application Layer Protocol",
        ],
        "provider": "deterministic-demo",
        "live": False,
        "message": "Local deterministic analysis is active.",
    }

def _clean_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return json.loads(text)

async def _gemini(prompt: str) -> Dict[str, Any]:
    key = os.getenv("GEMINI_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured")
    client = genai.Client(api_key=key)

    def call():
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json",
            ),
        )
        return response.text

    data = _clean_json(await __import__("asyncio").to_thread(call))
    return {**data, "provider": f"gemini:{GEMINI_MODEL}", "live": True}

async def _groq(prompt: str) -> Dict[str, Any]:
    key = os.getenv("GROQ_API_KEY", "").strip()
    if not key:
        raise RuntimeError("GROQ_API_KEY is not configured")

    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 700,
        "response_format": {"type": "json_object"},
    }
    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
            json=payload,
        )
        response.raise_for_status()
        data = response.json()
    content = data["choices"][0]["message"]["content"]
    result = _clean_json(content)
    return {**result, "provider": f"groq:{GROQ_MODEL}", "live": True}

@router.get("/status")
async def ai_status():
    return {
        "primary": PRIMARY,
        "gemini_configured": bool(os.getenv("GEMINI_API_KEY", "").strip()),
        "groq_configured": bool(os.getenv("GROQ_API_KEY", "").strip()),
        "gemini_model": GEMINI_MODEL,
        "groq_model": GROQ_MODEL,
        "fallback_enabled": FALLBACK_ENABLED,
    }

@router.post("/explain-demo")
async def explain_demo(payload: Dict[str, Any]):
    """
    One compact AI request for the demo incident.
    Gemini is tried first (or Groq if configured as primary), then the other
    provider, then deterministic local analysis. Results are cached per
    incident so repeated clicks do not repeatedly consume free-tier quota.
    """
    incident_id = f"{(payload.get('incident') or {}).get('id', 'SIM-0001')}::{payload.get('run_id', 'default')}"
    if incident_id in _demo_cache:
        cached = dict(_demo_cache[incident_id])
        cached["cached"] = True
        return cached

    prompt = (
        SYSTEM_PROMPT
        + "\nRequired JSON shape example:\n"
        + json.dumps(SCHEMA_HINT)
        + "\n\nSIMULATED INCIDENT DATA:\n"
        + json.dumps(payload, ensure_ascii=False)[:18000]
    )

    providers = ["gemini", "groq"] if PRIMARY != "groq" else ["groq", "gemini"]
    errors = []

    if FALLBACK_ENABLED:
        providers = providers
    else:
        providers = providers[:1]

    for provider in providers:
        try:
            result = await (_gemini(prompt) if provider == "gemini" else _groq(prompt))
            result["fallback_used"] = provider != PRIMARY
            _demo_cache[incident_id] = dict(result)
            return result
        except Exception as exc:
            logger.warning("AI provider %s unavailable: %s", provider, exc)
            errors.append(f"{provider}: {str(exc)[:180]}")

    result = _fallback()
    result["message"] = "Live providers unavailable; deterministic analysis kept the demo running."
    result["provider_errors"] = errors
    _demo_cache[incident_id] = dict(result)
    return result
