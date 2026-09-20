"""
SentinelX demo endpoints.
Records the analyst audit trail for the SIMULATED incident and pushes it over the WebSocket.
Nothing here touches the endpoint: all actions are simulation only.
"""
from collections import deque
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/demo", tags=["demo"])

_audit: deque = deque(maxlen=500)


class AuditEntry(BaseModel):
    phase: str
    action: str
    detail: Optional[str] = ""
    incident_id: str = "SIM-0001"
    actor: str = "system"


@router.get("/status")
async def demo_status():
    return {"mode": "simulation", "audit_entries": len(_audit)}


@router.get("/audit")
async def get_audit(limit: int = 200):
    return list(_audit)[-limit:]


@router.post("/audit")
async def add_audit(entry: AuditEntry):
    rec = entry.model_dump()
    rec["id"] = len(_audit) + 1
    rec["timestamp"] = datetime.now(timezone.utc).isoformat()
    rec["simulated"] = True
    _audit.append(rec)
    try:
        from api.main import ws_manager
        await ws_manager.broadcast({"type": "demo_audit", "data": rec})
    except Exception:
        pass
    return rec


@router.delete("/audit")
async def reset_audit():
    _audit.clear()
    return {"cleared": True}
