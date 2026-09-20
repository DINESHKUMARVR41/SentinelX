"""
Query Handler - Autonomous Querying System
Handles Gemini's autonomous queries for raw process data
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class QueryHandler:
    """Handles autonomous queries from Gemini"""
    
    QUERY_TYPES = {
        'QUERY_PROCESS': 'Query specific process details',
        'QUERY_TIMERANGE': 'Query events in time range',
        'QUERY_PATTERN': 'Query by pattern/behavior',
        'QUERY_NETWORK': 'Query network activity',
        'QUERY_FILES': 'Query file access patterns'
    }
    
    def __init__(self, state_manager):
        self.state_manager = state_manager
        
    async def handle_query(self, query: Dict[str, Any], 
                          investigation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Handle autonomous query from Gemini
        
        Query format:
        {
            "action": "QUERY_PROCESS",
            "process_id": 1234,
            "time_range": "last_5_minutes",
            "details": ["network", "file_access", "cpu"]
        }
        """
        action = query.get('action')
        
        if action not in self.QUERY_TYPES:
            return {'error': f'Unknown query action: {action}'}
            
        logger.info(f"🔍 Gemini query: {action} - {query}")
        
        # Route to appropriate handler
        if action == 'QUERY_PROCESS':
            result = await self._query_process(query)
        elif action == 'QUERY_TIMERANGE':
            result = await self._query_timerange(query)
        elif action == 'QUERY_PATTERN':
            result = await self._query_pattern(query)
        elif action == 'QUERY_NETWORK':
            result = await self._query_network(query)
        elif action == 'QUERY_FILES':
            result = await self._query_files(query)
        else:
            result = {'error': 'Not implemented'}
            
        # Log query
        await self._log_query(action, query, result, investigation_id)
        
        return result
        
    async def _query_process(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query specific process details - returns available data even if less than requested"""
        pid = query.get('process_id')
        time_range = query.get('time_range', 'last_5_minutes')
        details = query.get('details', ['all'])
        
        if not pid:
            return {'error': 'process_id required'}
            
        # Parse time range (but we'll return whatever data we have)
        requested_start = self._parse_time_range(time_range)
        
        # First, check what data we actually have for this process
        async with self.state_manager.db.execute("""
            SELECT MIN(collected_at) as earliest, MAX(collected_at) as latest, COUNT(*) as count
            FROM raw_process_events
            WHERE pid = ?
        """, (pid,)) as cursor:
            stats = await cursor.fetchone()
        
        if not stats or stats['count'] == 0:
            # Check if this PID exists in investigations (might have been triggered but data not captured)
            async with self.state_manager.db.execute("""
                SELECT process_name, triggered_at FROM investigations WHERE pid = ? LIMIT 1
            """, (pid,)) as cursor:
                inv = await cursor.fetchone()
            
            if inv:
                return {
                    'process_id': pid,
                    'found': False,
                    'message': f'Process {pid} ({inv["process_name"]}) was detected but raw event data was not captured. It may have terminated before data collection (<1 second lifetime) or access was denied.',
                    'investigation_exists': True,
                    'process_name': inv['process_name'],
                    'detected_at': inv['triggered_at']
                }
            else:
                return {
                    'process_id': pid,
                    'found': False,
                    'message': f'No data found for process {pid}. It may have terminated before monitoring started, or was not monitored.',
                    'investigation_exists': False
                }
        
        # Query ALL available events for this process (not just requested time range)
        async with self.state_manager.db.execute("""
            SELECT * FROM raw_process_events
            WHERE pid = ?
            ORDER BY collected_at DESC
            LIMIT 100
        """, (pid,)) as cursor:
            events = await cursor.fetchall()
            
        # Calculate actual time range of data
        actual_start = datetime.fromisoformat(stats['earliest'].replace('Z', ''))
        actual_end = datetime.fromisoformat(stats['latest'].replace('Z', ''))
        actual_duration = (actual_end - actual_start).total_seconds()
            
        # Process events based on requested details
        result = {
            'process_id': pid,
            'found': True,
            'requested_time_range': time_range,
            'actual_time_range': f'{actual_duration:.0f} seconds of data available',
            'data_coverage': f'From {actual_start.strftime("%H:%M:%S")} to {actual_end.strftime("%H:%M:%S")}',
            'event_count': len(events),
            'note': f'Returned all available data ({len(events)} events over {actual_duration:.0f}s)',
            'data': {}
        }
        
        # Extract requested details
        if 'all' in details or 'network' in details:
            result['data']['network'] = self._extract_network_data(events)
            
        if 'all' in details or 'file_access' in details:
            result['data']['file_access'] = self._extract_file_data(events)
            
        if 'all' in details or 'cpu' in details:
            result['data']['cpu_usage'] = self._extract_cpu_data(events)
            
        if 'all' in details or 'metadata' in details:
            latest = events[0]
            result['data']['metadata'] = {
                'process_name': latest['process_name'],
                'process_path': latest['process_path'],
                'parent_pid': latest['parent_pid'],
                'command_line': latest['command_line'],
                'user_name': latest['user_name']
            }
            
        return result
        
    async def _query_timerange(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query all events in time range"""
        time_range = query.get('time_range', 'last_1_minute')
        event_types = query.get('event_types', [])
        
        start_time = self._parse_time_range(time_range)
        
        # Build query
        sql = "SELECT * FROM raw_process_events WHERE collected_at >= ?"
        params = [start_time.isoformat()]
        
        if event_types:
            placeholders = ','.join('?' * len(event_types))
            sql += f" AND event_type IN ({placeholders})"
            params.extend(event_types)
            
        sql += " ORDER BY collected_at DESC LIMIT 500"
        
        async with self.state_manager.db.execute(sql, params) as cursor:
            events = await cursor.fetchall()
            
        return {
            'time_range': time_range,
            'event_count': len(events),
            'events': [dict(e) for e in events[:50]]  # Return first 50
        }
        
    async def _query_pattern(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query by behavior pattern"""
        pattern = query.get('pattern')
        time_range = query.get('time_range', 'last_10_minutes')
        
        start_time = self._parse_time_range(time_range)
        
        if pattern == 'shell_spawn':
            # Find shell processes
            async with self.state_manager.db.execute("""
                SELECT * FROM raw_process_events
                WHERE process_name IN ('powershell.exe', 'cmd.exe', 'bash', 'sh')
                AND collected_at >= ?
                ORDER BY collected_at DESC
                LIMIT 100
            """, (start_time.isoformat(),)) as cursor:
                events = await cursor.fetchall()
                
        elif pattern == 'high_network':
            # Find processes with many connections
            async with self.state_manager.db.execute("""
                SELECT * FROM raw_process_events
                WHERE event_type = 'NETWORK'
                AND collected_at >= ?
                ORDER BY collected_at DESC
                LIMIT 100
            """, (start_time.isoformat(),)) as cursor:
                events = await cursor.fetchall()
                
        elif pattern == 'suspicious_path':
            # Find processes from temp/unusual locations
            async with self.state_manager.db.execute("""
                SELECT * FROM raw_process_events
                WHERE (process_path LIKE '%Temp%' OR process_path LIKE '%AppData%')
                AND collected_at >= ?
                ORDER BY collected_at DESC
                LIMIT 100
            """, (start_time.isoformat(),)) as cursor:
                events = await cursor.fetchall()
        else:
            return {'error': f'Unknown pattern: {pattern}'}
            
        return {
            'pattern': pattern,
            'time_range': time_range,
            'matches': len(events),
            'events': [dict(e) for e in events[:20]]
        }
        
    async def _query_network(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query network activity"""
        time_range = query.get('time_range', 'last_5_minutes')
        min_connections = query.get('min_connections', 1)
        
        start_time = self._parse_time_range(time_range)
        
        async with self.state_manager.db.execute("""
            SELECT * FROM raw_process_events
            WHERE event_type = 'NETWORK'
            AND collected_at >= ?
            ORDER BY collected_at DESC
            LIMIT 200
        """, (start_time.isoformat(),)) as cursor:
            events = await cursor.fetchall()
            
        # Filter by connection count
        filtered = []
        for event in events:
            conns = json.loads(event['network_connections'])
            if len(conns) >= min_connections:
                filtered.append({
                    **dict(event),
                    'connection_count': len(conns),
                    'connections': conns
                })
                
        return {
            'time_range': time_range,
            'total_events': len(events),
            'filtered_count': len(filtered),
            'processes': filtered[:30]
        }
        
    async def _query_files(self, query: Dict[str, Any]) -> Dict[str, Any]:
        """Query file access patterns"""
        time_range = query.get('time_range', 'last_5_minutes')
        file_pattern = query.get('file_pattern', '')
        
        start_time = self._parse_time_range(time_range)
        
        async with self.state_manager.db.execute("""
            SELECT * FROM raw_process_events
            WHERE event_type = 'FILE_ACCESS'
            AND collected_at >= ?
            ORDER BY collected_at DESC
            LIMIT 200
        """, (start_time.isoformat(),)) as cursor:
            events = await cursor.fetchall()
            
        # Filter by file pattern if specified
        filtered = []
        for event in events:
            files = json.loads(event['open_files'])
            if file_pattern:
                matching_files = [f for f in files if file_pattern.lower() in f.lower()]
                if matching_files:
                    filtered.append({
                        **dict(event),
                        'matching_files': matching_files
                    })
            else:
                filtered.append({
                    **dict(event),
                    'files': files
                })
                
        return {
            'time_range': time_range,
            'file_pattern': file_pattern,
            'matches': len(filtered),
            'processes': filtered[:30]
        }
        
    def _parse_time_range(self, time_range: str) -> datetime:
        """Parse time range string to datetime"""
        now = datetime.utcnow()
        
        if time_range == 'last_1_minute':
            return now - timedelta(minutes=1)
        elif time_range == 'last_5_minutes':
            return now - timedelta(minutes=5)
        elif time_range == 'last_10_minutes':
            return now - timedelta(minutes=10)
        elif time_range == 'last_30_minutes':
            return now - timedelta(minutes=30)
        elif time_range == 'last_hour':
            return now - timedelta(hours=1)
        else:
            return now - timedelta(minutes=5)  # Default
            
    def _extract_network_data(self, events: List) -> Dict[str, Any]:
        """Extract network data from events"""
        all_connections = []
        unique_ips = set()
        
        for event in events:
            if event['network_connections']:
                conns = json.loads(event['network_connections'])
                all_connections.extend(conns)
                for conn in conns:
                    if conn.get('raddr'):
                        ip = conn['raddr'].split(':')[0]
                        unique_ips.add(ip)
                        
        return {
            'total_connections': len(all_connections),
            'unique_remote_ips': len(unique_ips),
            'recent_connections': all_connections[:10]
        }
        
    def _extract_file_data(self, events: List) -> Dict[str, Any]:
        """Extract file access data from events"""
        all_files = set()
        
        for event in events:
            if event['open_files']:
                files = json.loads(event['open_files'])
                all_files.update(files)
                
        return {
            'unique_files': len(all_files),
            'files': list(all_files)[:20]
        }
        
    def _extract_cpu_data(self, events: List) -> Dict[str, Any]:
        """Extract CPU usage data from events"""
        cpu_values = [e['cpu_percent'] for e in events if e['cpu_percent']]
        
        if not cpu_values:
            return {'average': 0, 'max': 0, 'samples': 0}
            
        return {
            'average': sum(cpu_values) / len(cpu_values),
            'max': max(cpu_values),
            'min': min(cpu_values),
            'samples': len(cpu_values)
        }
        
    async def _log_query(self, query_type: str, query_params: Dict, 
                        result: Dict, investigation_id: Optional[str]):
        """Log query to database"""
        await self.state_manager.db.execute("""
            INSERT INTO gemini_queries (
                query_type, query_params, result_count, result_data, investigation_id
            ) VALUES (?, ?, ?, ?, ?)
        """, (
            query_type,
            json.dumps(query_params),
            result.get('event_count', result.get('matches', 0)),
            json.dumps(result),
            investigation_id
        ))
        await self.state_manager.db.commit()
        
    def get_query_protocol_description(self) -> str:
        """Get description of query protocol for Gemini"""
        return """
**AUTONOMOUS QUERY PROTOCOL**

You can query raw process data autonomously using this protocol:

**Available Query Types:**

1. QUERY_PROCESS - Get detailed info about specific process
   {
     "action": "QUERY_PROCESS",
     "process_id": 1234,
     "time_range": "last_5_minutes",
     "details": ["network", "file_access", "cpu", "metadata"]
   }

2. QUERY_TIMERANGE - Get all events in time range
   {
     "action": "QUERY_TIMERANGE",
     "time_range": "last_10_minutes",
     "event_types": ["NETWORK", "FILE_ACCESS"]
   }

3. QUERY_PATTERN - Query by behavior pattern
   {
     "action": "QUERY_PATTERN",
     "pattern": "shell_spawn|high_network|suspicious_path",
     "time_range": "last_10_minutes"
   }

4. QUERY_NETWORK - Query network activity
   {
     "action": "QUERY_NETWORK",
     "time_range": "last_5_minutes",
     "min_connections": 5
   }

5. QUERY_FILES - Query file access patterns
   {
     "action": "QUERY_FILES",
     "time_range": "last_5_minutes",
     "file_pattern": ".exe"
   }

**Time Ranges:** last_1_minute, last_5_minutes, last_10_minutes, last_30_minutes, last_hour

**When to Query:**
- Summary shows suspicious pattern → Query for details
- Need historical context → Query time range
- Investigating specific PID → Query process
- Looking for related activity → Query pattern
"""
