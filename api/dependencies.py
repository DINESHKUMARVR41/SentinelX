"""
API Dependencies
"""

from agent.state_manager import StateManager
import aiosqlite
from pathlib import Path
from fastapi import HTTPException


# Separate read-only connection for API queries
_read_db = None


async def get_read_db() -> aiosqlite.Connection:
    """Get read-only database connection for API queries"""
    global _read_db
    
    if _read_db is None:
        db_path = Path("./database/procsee.db")
        _read_db = await aiosqlite.connect(
            str(db_path),
            timeout=30.0,
            check_same_thread=False
        )
        _read_db.row_factory = aiosqlite.Row
        # Read-only mode
        await _read_db.execute("PRAGMA query_only = ON")
        await _read_db.execute("PRAGMA busy_timeout = 30000")
    
    return _read_db


async def get_state_manager() -> StateManager:
    """Get state manager dependency from the running agent"""
    from api.main import agent
    
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized (demo mode)")
    
    return agent.state_manager
