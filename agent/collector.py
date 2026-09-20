"""
Forensic Collector
Gathers evidence from various system sources
"""

import psutil
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
import logging
import subprocess
import socket

logger = logging.getLogger(__name__)


class ForensicCollector:
    """Collects forensic evidence from system"""
    
    def __init__(self, state_manager, config):
        self.state_manager = state_manager
        self.config = config
        
    async def collect_process_tree(self, pid: int, inv_id: str) -> Dict[str, Any]:
        """Collect process tree information"""
        logger.info(f"Collecting process tree for PID {pid}")
        
        tree = {
            'target_pid': pid,
            'parent': None,
            'children': [],
            'siblings': [],
            'collected_at': datetime.utcnow().isoformat()
        }
        
        try:
            proc = psutil.Process(pid)
            
            # Get parent
            try:
                parent = proc.parent()
                if parent:
                    tree['parent'] = {
                        'pid': parent.pid,
                        'name': parent.name(),
                        'exe': parent.exe() if hasattr(parent, 'exe') else None,
                        'cmdline': ' '.join(parent.cmdline()) if hasattr(parent, 'cmdline') else None
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
            # Get children
            try:
                for child in proc.children(recursive=False):
                    tree['children'].append({
                        'pid': child.pid,
                        'name': child.name(),
                        'exe': child.exe() if hasattr(child, 'exe') else None,
                        'cmdline': ' '.join(child.cmdline()) if hasattr(child, 'cmdline') else None
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
                
        except psutil.NoSuchProcess:
            logger.warning(f"Process {pid} no longer exists")
            tree['error'] = 'Process terminated'
            
        # Store evidence
        await self.state_manager.add_evidence(
            inv_id, 'PROCESS_TREE', tree, importance='CRITICAL'
        )
        
        return tree
        
    async def collect_network_connections(self, pid: int, inv_id: str) -> Dict[str, Any]:
        """Collect network connection information"""
        logger.info(f"Collecting network connections for PID {pid}")
        
        connections = {
            'pid': pid,
            'connections': [],
            'listening_ports': [],
            'collected_at': datetime.utcnow().isoformat()
        }
        
        try:
            proc = psutil.Process(pid)
            conns = proc.connections()
            
            for conn in conns:
                conn_data = {
                    'fd': conn.fd,
                    'family': str(conn.family),
                    'type': str(conn.type),
                    'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                    'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                    'status': conn.status
                }
                
                if conn.status == 'LISTEN':
                    connections['listening_ports'].append(conn_data)
                else:
                    connections['connections'].append(conn_data)
                    
        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            connections['error'] = str(e)
            
        # Store evidence
        await self.state_manager.add_evidence(
            inv_id, 'NETWORK_CONNECTIONS', connections, 
            importance='CRITICAL' if len(connections['connections']) > 0 else 'RELEVANT'
        )
        
        return connections
        
    async def collect_filesystem_activity(self, pid: int, inv_id: str) -> Dict[str, Any]:
        """Collect filesystem activity"""
        logger.info(f"Collecting filesystem activity for PID {pid}")
        
        fs_data = {
            'pid': pid,
            'open_files': [],
            'cwd': None,
            'collected_at': datetime.utcnow().isoformat()
        }
        
        try:
            proc = psutil.Process(pid)
            
            # Get current working directory
            try:
                fs_data['cwd'] = proc.cwd()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
                
            # Get open files
            try:
                for f in proc.open_files():
                    fs_data['open_files'].append({
                        'path': f.path,
                        'fd': f.fd
                    })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
                
        except psutil.NoSuchProcess:
            fs_data['error'] = 'Process terminated'
            
        # Store evidence
        await self.state_manager.add_evidence(
            inv_id, 'FILE_SYSTEM', fs_data, importance='RELEVANT'
        )
        
        return fs_data
