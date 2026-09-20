"""
Interval Collector - Autonomous Querying System
Creates 1-minute summaries from real-time event data for Gemini analysis
"""

import asyncio
import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class IntervalCollector:
    """Creates 1-minute summaries from real-time process event data"""
    
    def __init__(self, state_manager, config):
        self.state_manager = state_manager
        self.config = config
        self.running = False
        self.summarization_task: Optional[asyncio.Task] = None
        
        # Storage management settings (can be overridden from database config)
        self.max_storage_mb = 1024  # Default 1GB limit
        self.cleanup_threshold_mb = 900  # Default cleanup at 900MB
        self.cleanup_amount_mb = 100  # Default delete 100MB worth of old data
        
    async def _load_storage_config(self):
        """Load storage configuration from database"""
        try:
            async with self.state_manager.db.execute(
                "SELECT max_storage_mb, cleanup_threshold_mb, cleanup_amount_mb FROM agent_config WHERE id = 1"
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    self.max_storage_mb = row['max_storage_mb'] or 1024
                    self.cleanup_threshold_mb = row['cleanup_threshold_mb'] or 900
                    self.cleanup_amount_mb = row['cleanup_amount_mb'] or 100
                    logger.info(f"📊 Storage config loaded: max={self.max_storage_mb}MB, threshold={self.cleanup_threshold_mb}MB, cleanup={self.cleanup_amount_mb}MB")
        except Exception as e:
            logger.warning(f"Could not load storage config, using defaults: {e}")
        
    async def start(self):
        """Start interval collection"""
        if self.running:
            return
        
        # Load storage configuration from database
        await self._load_storage_config()
            
        self.running = True
        logger.info("📊 Interval collector started (1-minute summaries from real-time events)")
        
        # Only start summarization task (raw collection now done by event monitor)
        self.summarization_task = asyncio.create_task(self._summarization_loop())
        
    async def stop(self):
        """Stop interval collection"""
        self.running = False
        
        if self.summarization_task:
            self.summarization_task.cancel()
            try:
                await self.summarization_task
            except asyncio.CancelledError:
                pass
                
        logger.info("Interval collector stopped")
        
    async def _summarization_loop(self):
        """Create 1-minute summaries from real-time event data"""
        while self.running:
            try:
                logger.info("⏰ Waiting 60 seconds for next summary...")
                await asyncio.sleep(60)  # Wait 1 minute
                logger.info("⏰ 60 seconds elapsed, creating summary now...")
                await self._create_interval_summary()
                
                # Check storage size and cleanup if needed
                await self._check_and_cleanup_by_size()
                
            except Exception as e:
                logger.error(f"Summarization loop error: {e}", exc_info=True)
                
    async def _create_interval_summary(self):
        """Create 1-minute summary from real-time event data"""
        try:
            # Use UTC time consistently
            interval_end = datetime.utcnow()
            interval_start = interval_end - timedelta(minutes=1)
            
            # Format for logging (local time for readability)
            local_start = datetime.now() - timedelta(minutes=1)
            local_end = datetime.now()
            
            logger.info(f"📝 Creating interval summary: {local_start.strftime('%H:%M:%S')} - {local_end.strftime('%H:%M:%S')} (local time)")
            logger.info(f"   UTC range: {interval_start.isoformat()} - {interval_end.isoformat()}")
            
            # Query raw events from last minute using UTC timestamps
            query = """
                SELECT * FROM raw_process_events
                WHERE collected_at >= ? AND collected_at < ?
                ORDER BY collected_at
            """
            params = (interval_start.strftime('%Y-%m-%d %H:%M:%S'), interval_end.strftime('%Y-%m-%d %H:%M:%S'))
            
            logger.info(f"   Query params: {params}")
            
            async with self.state_manager.db.execute(query, params) as cursor:
                events = await cursor.fetchall()
                
            logger.info(f"   Found {len(events)} events in this interval")
                
            if not events:
                logger.warning(f"⚠️ No events in interval {local_start.strftime('%H:%M:%S')} - {local_end.strftime('%H:%M:%S')}")
                return
                
            # Analyze events
            pids_seen = set()
            network_activity = []
            file_activity = []
            high_cpu = []
            suspicious_patterns = []
            registry_modifications = []
            scheduled_tasks = []
            process_activities = {}  # Track per-process activities
            
            for event in events:
                pid = event['pid']
                pids_seen.add(pid)
                
                # Initialize process tracking
                if pid not in process_activities:
                    process_activities[pid] = {
                        'name': event['process_name'],
                        'path': event['process_path'],
                        'network_connections': 0,
                        'files_accessed': 0,
                        'high_cpu': False,
                        'registry_modified': False,
                        'scheduled_task_created': False,
                        'suspicious_cmdline': False,
                        'parent_pid': event['parent_pid']
                    }
                
                # High CPU
                if event['cpu_percent'] > 50:
                    high_cpu.append({
                        'pid': pid,
                        'name': event['process_name'],
                        'cpu': event['cpu_percent']
                    })
                    process_activities[pid]['high_cpu'] = True
                    
                # Network activity
                if event['event_type'] == 'NETWORK' or event['network_connections']:
                    conns = json.loads(event['network_connections']) if event['network_connections'] else []
                    if conns:
                        network_activity.append({
                            'pid': pid,
                            'name': event['process_name'],
                            'connections': len(conns)
                        })
                        process_activities[pid]['network_connections'] += len(conns)
                        
                # File access
                if event['event_type'] == 'FILE_ACCESS' or event['open_files']:
                    files = json.loads(event['open_files']) if event['open_files'] else []
                    if files:
                        file_activity.append({
                            'pid': pid,
                            'name': event['process_name'],
                            'files': len(files)
                        })
                        process_activities[pid]['files_accessed'] += len(files)
                        
                # Suspicious patterns
                if event['process_name'] in ['powershell.exe', 'cmd.exe', 'wscript.exe']:
                    if event['parent_pid']:
                        suspicious_patterns.append({
                            'pattern': 'shell_spawn',
                            'pid': pid,
                            'name': event['process_name'],
                            'parent': event['parent_pid']
                        })
                        
                # Check for suspicious command lines
                if event['command_line']:
                    cmdline = event['command_line'].lower()
                    if any(keyword in cmdline for keyword in ['invoke-expression', 'downloadstring', 'bypass', 'hidden', 'encoded']):
                        suspicious_patterns.append({
                            'pattern': 'suspicious_cmdline',
                            'pid': pid,
                            'name': event['process_name'],
                            'cmdline': event['command_line'][:100]
                        })
                        process_activities[pid]['suspicious_cmdline'] = True
                        
                # Check for registry modifications (Windows-specific patterns)
                if event['process_name'] in ['reg.exe', 'regedit.exe'] or (event['command_line'] and 'reg add' in event['command_line'].lower()):
                    registry_modifications.append({
                        'pid': pid,
                        'name': event['process_name']
                    })
                    process_activities[pid]['registry_modified'] = True
                    
                # Check for scheduled task creation
                if event['process_name'] == 'schtasks.exe' or (event['command_line'] and 'schtasks' in event['command_line'].lower()):
                    scheduled_tasks.append({
                        'pid': pid,
                        'name': event['process_name']
                    })
                    process_activities[pid]['scheduled_task_created'] = True
                        
            # Create summary text
            summary_text = self._generate_summary_text(
                len(pids_seen), len(network_activity), len(file_activity), 
                len(high_cpu), len(suspicious_patterns), len(registry_modifications),
                len(scheduled_tasks)
            )
            
            # Insert summary with retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    # Try to insert with process_activities column (new schema)
                    try:
                        await self.state_manager.db.execute("""
                            INSERT INTO summary_intervals (
                                interval_start, interval_end, total_processes,
                                new_processes, terminated_processes, suspicious_patterns,
                                high_cpu_processes, high_network_processes, unusual_file_access,
                                summary_text, process_activities
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            interval_start.isoformat(),
                            interval_end.isoformat(),
                            len(pids_seen),
                            0,  # TODO: Track new processes
                            0,  # TODO: Track terminated
                            json.dumps(suspicious_patterns),
                            json.dumps(high_cpu[:5]),  # Top 5
                            json.dumps(network_activity[:5]),
                            json.dumps(file_activity[:5]),
                            summary_text,
                            json.dumps(process_activities)
                        ))
                    except Exception as schema_error:
                        # Fallback to old schema if process_activities column doesn't exist
                        if "no column named process_activities" in str(schema_error).lower() or "no such column" in str(schema_error).lower():
                            logger.warning("⚠️ Database schema missing process_activities column, using old schema")
                            await self.state_manager.db.execute("""
                                INSERT INTO summary_intervals (
                                    interval_start, interval_end, total_processes,
                                    new_processes, terminated_processes, suspicious_patterns,
                                    high_cpu_processes, high_network_processes, unusual_file_access,
                                    summary_text
                                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                interval_start.isoformat(),
                                interval_end.isoformat(),
                                len(pids_seen),
                                0,  # TODO: Track new processes
                                0,  # TODO: Track terminated
                                json.dumps(suspicious_patterns),
                                json.dumps(high_cpu[:5]),  # Top 5
                                json.dumps(network_activity[:5]),
                                json.dumps(file_activity[:5]),
                                summary_text
                            ))
                        else:
                            raise
                    
                    await self.state_manager.db.commit()
                    break
                except Exception as e:
                    if "database is locked" in str(e) and attempt < max_retries - 1:
                        await asyncio.sleep(0.1 * (attempt + 1))
                        continue
                    else:
                        raise
            
            logger.info(f"✅ Summary created: {len(pids_seen)} processes, {len(suspicious_patterns)} suspicious, {len(registry_modifications)} reg mods, {len(scheduled_tasks)} tasks")
            
        except Exception as e:
            logger.error(f"Failed to create interval summary: {e}", exc_info=True)
        
    def _generate_summary_text(self, total_procs: int, network_count: int, 
                               file_count: int, high_cpu_count: int, 
                               suspicious_count: int, registry_count: int = 0,
                               scheduled_task_count: int = 0) -> str:
        """Generate human-readable summary"""
        parts = [f"{total_procs} active processes"]
        
        if network_count > 0:
            parts.append(f"{network_count} with network activity")
        if file_count > 0:
            parts.append(f"{file_count} accessing files")
        if high_cpu_count > 0:
            parts.append(f"{high_cpu_count} high CPU usage")
        if registry_count > 0:
            parts.append(f"{registry_count} registry modifications")
        if scheduled_task_count > 0:
            parts.append(f"{scheduled_task_count} scheduled tasks")
        if suspicious_count > 0:
            parts.append(f"⚠️ {suspicious_count} suspicious patterns")
            
        return ", ".join(parts)
        
    async def _check_and_cleanup_by_size(self):
        """Check storage size and cleanup old data if approaching limit"""
        try:
            # Get current database size
            async with self.state_manager.db.execute("""
                SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()
            """) as cursor:
                result = await cursor.fetchone()
                db_size_bytes = result[0] if result else 0
                db_size_mb = db_size_bytes / (1024 * 1024)
            
            logger.info(f"📊 Database size: {db_size_mb:.2f} MB / {self.max_storage_mb} MB")
            
            # If approaching limit, cleanup old data
            if db_size_mb >= self.cleanup_threshold_mb:
                logger.warning(f"⚠️ Storage approaching limit ({db_size_mb:.2f} MB >= {self.cleanup_threshold_mb} MB)")
                logger.info(f"🗑️ Cleaning up {self.cleanup_amount_mb} MB worth of old data...")
                
                await self._cleanup_old_intervals()
                
                # Check size again
                async with self.state_manager.db.execute("""
                    SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()
                """) as cursor:
                    result = await cursor.fetchone()
                    new_size_mb = (result[0] if result else 0) / (1024 * 1024)
                
                freed_mb = db_size_mb - new_size_mb
                logger.info(f"✅ Cleanup complete: {freed_mb:.2f} MB freed, new size: {new_size_mb:.2f} MB")
            
        except Exception as e:
            logger.error(f"Error checking storage size: {e}", exc_info=True)
    
    async def _cleanup_old_intervals(self):
        """Delete oldest intervals to free up space"""
        try:
            # Get PIDs from active investigations (don't delete their data!)
            async with self.state_manager.db.execute("""
                SELECT pid FROM investigations WHERE is_active = 1
            """) as cursor:
                active_pids = [row[0] for row in await cursor.fetchall()]
            
            if active_pids:
                logger.info(f"🔒 Protecting data for {len(active_pids)} active investigations")
            
            # Find oldest events (excluding active investigation PIDs)
            # Delete approximately cleanup_amount_mb worth of data
            # Estimate: ~1KB per event, so 100MB = ~100,000 events
            events_to_delete = int(self.cleanup_amount_mb * 1024)
            
            if active_pids:
                placeholders = ','.join('?' * len(active_pids))
                query = f"""
                    DELETE FROM raw_process_events 
                    WHERE id IN (
                        SELECT id FROM raw_process_events 
                        WHERE pid NOT IN ({placeholders})
                        ORDER BY collected_at ASC 
                        LIMIT ?
                    )
                """
                params = (*active_pids, events_to_delete)
            else:
                query = """
                    DELETE FROM raw_process_events 
                    WHERE id IN (
                        SELECT id FROM raw_process_events 
                        ORDER BY collected_at ASC 
                        LIMIT ?
                    )
                """
                params = (events_to_delete,)
            
            async with self.state_manager.db.execute(query, params) as cursor:
                deleted = cursor.rowcount
            
            await self.state_manager.db.commit()
            
            # Vacuum to reclaim space
            await self.state_manager.db.execute("VACUUM")
            
            logger.info(f"🗑️ Deleted {deleted} old events (protected {len(active_pids)} active investigations)")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}", exc_info=True)
    
    async def _cleanup_old_data(self):
        """Legacy method - now redirects to size-based cleanup"""
        await self._check_and_cleanup_by_size()
