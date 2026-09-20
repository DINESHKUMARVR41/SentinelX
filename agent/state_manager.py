"""
State Manager - Marathon Agent Capability
Handles SQLite persistence, checkpointing, and resume logic
"""

import aiosqlite
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class StateManager:
    """Manages investigation state persistence"""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.db: Optional[aiosqlite.Connection] = None
        
    async def initialize(self):
        """Initialize database connection and schema"""
        # Ensure database directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Connect to database with optimized settings for concurrent access
        self.db = await aiosqlite.connect(
            self.db_path,
            timeout=60.0  # Longer timeout for concurrent access
        )
        self.db.row_factory = aiosqlite.Row
        
        # Enable WAL mode for better concurrent access
        await self.db.execute("PRAGMA journal_mode=WAL")
        await self.db.execute("PRAGMA synchronous=NORMAL")
        await self.db.execute("PRAGMA cache_size=10000")
        await self.db.execute("PRAGMA temp_store=MEMORY")
        await self.db.execute("PRAGMA busy_timeout=60000")  # 60 second busy timeout
        await self.db.execute("PRAGMA wal_autocheckpoint=1000")  # Checkpoint every 1000 pages
        await self.db.commit()
        
        # Load and execute schema only if tables don't exist
        schema_path = Path(__file__).parent.parent / "database" / "schema.sql"
        if schema_path.exists():
            # Check if tables exist
            async with self.db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='investigations'"
            ) as cursor:
                exists = await cursor.fetchone()
            
            if not exists:
                # Database is new, create schema
                with open(schema_path, 'r') as f:
                    schema = f.read()
                    # Execute statements one by one to avoid index conflicts
                    for statement in schema.split(';'):
                        statement = statement.strip()
                        if statement:
                            try:
                                await self.db.execute(statement)
                            except Exception as e:
                                # Ignore "already exists" errors
                                if "already exists" not in str(e):
                                    raise
                await self.db.commit()
            
        logger.info(f"Database initialized: {self.db_path}")
        
    async def close(self):
        """Close database connection"""
        if self.db:
            await self.db.close()
            
    async def create_investigation(self, investigation_data: Dict[str, Any]) -> str:
        """Create new investigation record"""
        inv_id = investigation_data.get('id')
        
        await self.db.execute("""
            INSERT INTO investigations (
                id, pid, process_name, process_path, process_hash,
                parent_pid, parent_name, command_line, user_name,
                triggered_at, status, current_phase, config_snapshot
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inv_id,
            investigation_data['pid'],
            investigation_data['process_name'],
            investigation_data.get('process_path'),
            investigation_data.get('process_hash'),
            investigation_data.get('parent_pid'),
            investigation_data.get('parent_name'),
            investigation_data.get('command_line'),
            investigation_data.get('user_name'),
            investigation_data['triggered_at'],
            'TRIGGERED',
            'TRIGGERED',
            json.dumps(investigation_data.get('config_snapshot', {}))
        ))
        await self.db.commit()
        
        logger.info(f"Created investigation: {inv_id}")
        return inv_id
        
    async def update_investigation(self, inv_id: str, updates: Dict[str, Any]):
        """Update investigation fields"""
        set_clauses = []
        values = []
        
        for key, value in updates.items():
            if key in ['gemini_analysis', 'config_snapshot'] and isinstance(value, (dict, list)):
                value = json.dumps(value)
            set_clauses.append(f"{key} = ?")
            values.append(value)
            
        set_clauses.append("updated_at = ?")
        values.append(datetime.utcnow().isoformat())
        values.append(inv_id)
        
        query = f"UPDATE investigations SET {', '.join(set_clauses)} WHERE id = ?"
        await self.db.execute(query, values)
        await self.db.commit()
        
    async def get_investigation(self, inv_id: str) -> Optional[Dict[str, Any]]:
        """Get investigation by ID"""
        async with self.db.execute(
            "SELECT * FROM investigations WHERE id = ?", (inv_id,)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
            
    async def get_active_investigations(self) -> List[Dict[str, Any]]:
        """Get all active investigations"""
        async with self.db.execute(
            "SELECT * FROM investigations WHERE is_active = 1 ORDER BY triggered_at DESC"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def get_incomplete_investigations(self) -> List[Dict[str, Any]]:
        """Get investigations that need to be resumed"""
        async with self.db.execute(
            "SELECT * FROM investigations WHERE status != 'COMPLETED' AND is_active = 1"
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def add_evidence(self, inv_id: str, evidence_type: str, 
                          content: Any, importance: str = "RELEVANT",
                          file_path: Optional[str] = None) -> int:
        """Add evidence to investigation"""
        content_str = json.dumps(content) if isinstance(content, (dict, list)) else str(content)
        content_hash = hashlib.sha256(content_str.encode()).hexdigest()
        
        cursor = await self.db.execute("""
            INSERT INTO evidence_log (
                investigation_id, evidence_type, content, 
                file_path, importance, content_hash
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (inv_id, evidence_type, content_str, file_path, importance, content_hash))
        await self.db.commit()
        
        return cursor.lastrowid
        
    async def get_evidence(self, inv_id: str, 
                          evidence_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get evidence for investigation"""
        if evidence_type:
            query = "SELECT * FROM evidence_log WHERE investigation_id = ? AND evidence_type = ? ORDER BY collected_at"
            params = (inv_id, evidence_type)
        else:
            query = "SELECT * FROM evidence_log WHERE investigation_id = ? ORDER BY collected_at"
            params = (inv_id,)
            
        async with self.db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
            
    async def create_snapshot(self, inv_id: str, phase: str, snapshot_data: Dict[str, Any]) -> int:
        """Create investigation checkpoint snapshot"""
        cursor = await self.db.execute("""
            INSERT INTO investigation_snapshots (investigation_id, phase, snapshot_data)
            VALUES (?, ?, ?)
        """, (inv_id, phase, json.dumps(snapshot_data)))
        await self.db.commit()
        
        logger.debug(f"Created snapshot for {inv_id} at phase {phase}")
        return cursor.lastrowid
        
    async def get_latest_snapshot(self, inv_id: str) -> Optional[Dict[str, Any]]:
        """Get most recent snapshot for investigation"""
        async with self.db.execute("""
            SELECT * FROM investigation_snapshots 
            WHERE investigation_id = ? 
            ORDER BY created_at DESC LIMIT 1
        """, (inv_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                data = dict(row)
                data['snapshot_data'] = json.loads(data['snapshot_data'])
                return data
            return None
            
    async def add_note(self, inv_id: str, note: str, created_by: str = "analyst") -> int:
        """Add analyst note to investigation"""
        cursor = await self.db.execute("""
            INSERT INTO investigation_notes (investigation_id, note, created_by)
            VALUES (?, ?, ?)
        """, (inv_id, note, created_by))
        await self.db.commit()
        return cursor.lastrowid
        
    async def log_system_event(self, event_type: str, message: str, details: Optional[Dict] = None):
        """Log system event"""
        await self.db.execute("""
            INSERT INTO system_events (event_type, message, details)
            VALUES (?, ?, ?)
        """, (event_type, message, json.dumps(details) if details else None))
        await self.db.commit()


async def init_database(db_path: str = "./database/procsee.db"):
    """Initialize database from schema"""
    manager = StateManager(db_path)
    await manager.initialize()
    await manager.close()
    return manager
