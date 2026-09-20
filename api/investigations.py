"""
Investigation API Endpoints
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
import logging

from api.dependencies import get_state_manager, get_read_db

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/investigations", tags=["investigations"])


class InvestigationResponse(BaseModel):
    """Investigation response model"""
    id: str
    pid: int
    process_name: str
    process_path: Optional[str]
    parent_name: Optional[str]
    triggered_at: str
    status: str
    current_phase: str
    risk_score: float
    risk_level: str
    confidence: float
    summary: Optional[str]
    is_active: bool


class EvidenceResponse(BaseModel):
    """Evidence response model"""
    id: int
    investigation_id: str
    collected_at: str
    evidence_type: str
    importance: str
    content: str


class NoteCreate(BaseModel):
    """Note creation model"""
    note: str
    created_by: str = "analyst"


@router.get("/", response_model=List[InvestigationResponse])
async def list_investigations(
    active_only: bool = False,
    limit: int = 100,
    state_manager = Depends(get_state_manager)
):
    """List all investigations"""
    if active_only:
        investigations = await state_manager.get_active_investigations()
    else:
        # Get all investigations
        async with state_manager.db.execute(
            "SELECT * FROM investigations ORDER BY triggered_at DESC LIMIT ?",
            (limit,)
        ) as cursor:
            rows = await cursor.fetchall()
            investigations = [dict(row) for row in rows]
    
    return investigations


@router.get("/{inv_id}", response_model=InvestigationResponse)
async def get_investigation(
    inv_id: str,
    state_manager = Depends(get_state_manager)
):
    """Get specific investigation"""
    inv = await state_manager.get_investigation(inv_id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    return inv


@router.get("/{inv_id}/evidence", response_model=List[EvidenceResponse])
async def get_evidence(
    inv_id: str,
    evidence_type: Optional[str] = None,
    state_manager = Depends(get_state_manager)
):
    """Get evidence for investigation"""
    evidence = await state_manager.get_evidence(inv_id, evidence_type)
    return evidence


@router.get("/{inv_id}/timeline")
async def get_timeline(
    inv_id: str,
    state_manager = Depends(get_state_manager)
):
    """Get chronological timeline of investigation"""
    evidence = await state_manager.get_evidence(inv_id)
    
    # Sort by collected_at
    timeline = sorted(evidence, key=lambda x: x['collected_at'])
    
    return {
        "investigation_id": inv_id,
        "events": timeline
    }


@router.post("/{inv_id}/notes")
async def add_note(
    inv_id: str,
    note_data: NoteCreate,
    state_manager = Depends(get_state_manager)
):
    """Add analyst note to investigation"""
    note_id = await state_manager.add_note(
        inv_id, 
        note_data.note, 
        note_data.created_by
    )
    
    return {
        "id": note_id,
        "investigation_id": inv_id,
        "note": note_data.note
    }


@router.post("/{inv_id}/close")
async def close_investigation(
    inv_id: str,
    state_manager = Depends(get_state_manager)
):
    """Mark investigation as closed"""
    await state_manager.update_investigation(inv_id, {
        'status': 'COMPLETED',
        'is_active': False,
        'completed_at': datetime.utcnow().isoformat()
    })
    
    return {"message": "Investigation closed", "investigation_id": inv_id}


@router.get("/{inv_id}/analysis")
async def get_analysis(
    inv_id: str,
    state_manager = Depends(get_state_manager)
):
    """Get Gemini analysis for investigation"""
    inv = await state_manager.get_investigation(inv_id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    import json
    analysis = json.loads(inv['gemini_analysis']) if inv.get('gemini_analysis') else None
    
    return {
        "investigation_id": inv_id,
        "risk_score": inv.get('risk_score'),
        "risk_level": inv.get('risk_level'),
        "confidence": inv.get('confidence'),
        "analysis": analysis
    }


@router.get("/{inv_id}/detailed-report")
async def get_detailed_report(
    inv_id: str,
    state_manager = Depends(get_state_manager)
):
    """Get detailed Markdown report for investigation"""
    inv = await state_manager.get_investigation(inv_id)
    
    if not inv:
        raise HTTPException(status_code=404, detail="Investigation not found")
    
    detailed_report_md = inv.get('detailed_report_md')
    
    if not detailed_report_md:
        raise HTTPException(status_code=404, detail="Detailed report not yet generated")
    
    return {
        "investigation_id": inv_id,
        "report_markdown": detailed_report_md,
        "generated_at": inv.get('report_generated_at')
    }


# Autonomous Querying System Endpoints

@router.get("/intervals/summaries")
async def get_interval_summaries(
    limit: int = 20,
    db = Depends(get_read_db)
):
    """Get interval summaries using read-only connection"""
    logger.info(f"📊 API: Fetching interval summaries (limit={limit})")
    async with db.execute("""
        SELECT * FROM summary_intervals
        ORDER BY interval_start DESC
        LIMIT ?
    """, (limit,)) as cursor:
        rows = await cursor.fetchall()
        result = [dict(row) for row in rows]
        logger.info(f"📊 API: Returning {len(result)} interval summaries")
        if len(result) > 0:
            logger.info(f"📊 API: Latest summary: {result[0].get('interval_start')} - {result[0].get('summary_text')}")
        return result


@router.get("/intervals/raw-events")
async def get_raw_events(
    pid: Optional[int] = None,
    limit: int = 100,
    db = Depends(get_read_db)
):
    """Get raw process events using read-only connection"""
    if pid:
        query = "SELECT * FROM raw_process_events WHERE pid = ? ORDER BY collected_at DESC LIMIT ?"
        params = (pid, limit)
    else:
        query = "SELECT * FROM raw_process_events ORDER BY collected_at DESC LIMIT ?"
        params = (limit,)
        
    async with db.execute(query, params) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/query")
async def autonomous_query(
    query: dict,
    investigation_id: Optional[str] = None,
    state_manager = Depends(get_state_manager)
):
    """Execute autonomous query (for testing Gemini queries)"""
    from agent.query_handler import QueryHandler
    query_handler = QueryHandler(state_manager)
    result = await query_handler.handle_query(query, investigation_id)
    return result


@router.get("/query/protocol")
async def get_query_protocol(
    state_manager = Depends(get_state_manager)
):
    """Get query protocol description"""
    from agent.query_handler import QueryHandler
    query_handler = QueryHandler(state_manager)
    return {
        "protocol": query_handler.get_query_protocol_description(),
        "available_queries": list(query_handler.QUERY_TYPES.keys())
    }


@router.get("/gemini/queries")
async def get_gemini_queries(
    limit: int = 50,
    db = Depends(get_read_db)
):
    """Get Gemini's autonomous queries log using read-only connection"""
    async with db.execute("""
        SELECT * FROM gemini_queries
        ORDER BY created_at DESC
        LIMIT ?
    """, (limit,)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.post("/intervals/{interval_id}/generate-report")
async def generate_interval_report(
    interval_id: int,
    state_manager = Depends(get_state_manager)
):
    """Generate detailed Markdown report for an interval analysis using Gemini"""
    from agent.gemini_client import GeminiClient
    from agent.config import load_config
    
    # Get interval summary
    async with state_manager.db.execute(
        "SELECT * FROM summary_intervals WHERE id = ?",
        (interval_id,)
    ) as cursor:
        row = await cursor.fetchone()
    
    if not row:
        raise HTTPException(status_code=404, detail="Interval not found")
    
    interval = dict(row)
    
    # Check if report already exists
    if interval.get('detailed_report_md'):
        return {
            "interval_id": interval_id,
            "report": interval['detailed_report_md'],
            "generated_at": interval.get('report_generated_at'),
            "cached": True
        }
    
    # Get Gemini response
    gemini_response = json.loads(interval['gemini_response']) if interval.get('gemini_response') else {}
    
    # Get queries executed during this interval
    interval_start = interval['interval_start']
    interval_end = interval['interval_end']
    
    async with state_manager.db.execute("""
        SELECT * FROM gemini_queries
        WHERE created_at >= ? AND created_at <= ?
        ORDER BY created_at
    """, (interval_start, interval_end)) as cursor:
        queries = await cursor.fetchall()
        query_list = [dict(row) for row in queries]
    
    # Initialize Gemini client
    config = load_config()
    gemini_client = GeminiClient(config, None)
    
    # Generate detailed report
    report_markdown = await gemini_client.generate_interval_detailed_report(
        interval,
        gemini_response,
        query_list
    )
    
    # Store report in database
    await state_manager.db.execute("""
        UPDATE summary_intervals
        SET detailed_report_md = ?, report_generated_at = ?
        WHERE id = ?
    """, (report_markdown, datetime.utcnow().isoformat(), interval_id))
    await state_manager.db.commit()
    
    return {
        "interval_id": interval_id,
        "report": report_markdown,
        "generated_at": datetime.utcnow().isoformat(),
        "cached": False
    }


@router.get("/stats/system-metrics")
async def get_system_metrics(
    state_manager = Depends(get_state_manager)
):
    """Get system resource metrics"""
    import psutil
    import os
    
    # Get PROCSee process metrics
    process = psutil.Process(os.getpid())
    cpu_percent = process.cpu_percent(interval=0.1)
    memory_info = process.memory_info()
    memory_mb = memory_info.rss / 1024 / 1024
    
    # Get database size
    db_path = state_manager.db_path
    db_size_mb = 0
    if os.path.exists(db_path):
        db_size_mb = os.path.getsize(db_path) / 1024 / 1024
        # Add WAL files
        wal_path = f"{db_path}-wal"
        if os.path.exists(wal_path):
            db_size_mb += os.path.getsize(wal_path) / 1024 / 1024
    
    return {
        "cpu_percent": round(cpu_percent, 2),
        "memory_mb": round(memory_mb, 2),
        "database_size_mb": round(db_size_mb, 2),
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get("/stats/activity-timeline")
async def get_activity_timeline(
    hours: int = 24,
    db = Depends(get_read_db)
):
    """Get investigation activity over time"""
    async with db.execute("""
        SELECT 
            strftime('%Y-%m-%d %H:00:00', triggered_at) as hour,
            risk_level,
            COUNT(*) as count
        FROM investigations
        WHERE triggered_at >= datetime('now', '-' || ? || ' hours')
        GROUP BY hour, risk_level
        ORDER BY hour ASC
    """, (hours,)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/stats/risk-distribution")
async def get_risk_distribution(
    db = Depends(get_read_db)
):
    """Get risk level distribution"""
    async with db.execute("""
        SELECT 
            risk_level,
            COUNT(*) as count
        FROM investigations
        GROUP BY risk_level
    """) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]


@router.get("/stats/top-processes")
async def get_top_processes(
    limit: int = 10,
    db = Depends(get_read_db)
):
    """Get most frequently investigated processes"""
    async with db.execute("""
        SELECT 
            process_name,
            COUNT(*) as investigation_count,
            AVG(risk_score) as avg_risk_score,
            MAX(risk_level) as max_risk_level
        FROM investigations
        GROUP BY process_name
        ORDER BY investigation_count DESC
        LIMIT ?
    """, (limit,)) as cursor:
        rows = await cursor.fetchall()
        return [dict(row) for row in rows]
