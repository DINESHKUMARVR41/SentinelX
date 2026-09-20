"""
Evidence Processor
Summarizes and prioritizes evidence for Gemini analysis
"""

from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class EvidenceProcessor:
    """Processes and summarizes evidence"""
    
    def summarize_evidence(self, evidence_items: List[Dict[str, Any]]) -> str:
        """
        Convert raw evidence into narrative summaries
        This is critical for staying within token limits
        """
        summary_parts = []
        
        # Group by type
        by_type = {}
        for item in evidence_items:
            etype = item['evidence_type']
            if etype not in by_type:
                by_type[etype] = []
            by_type[etype].append(item)
            
        # Summarize each type
        for etype, items in by_type.items():
            if etype == 'PROCESS_TREE':
                summary_parts.append(self._summarize_process_tree(items))
            elif etype == 'NETWORK_CONNECTIONS':
                summary_parts.append(self._summarize_network(items))
            elif etype == 'FILE_SYSTEM':
                summary_parts.append(self._summarize_filesystem(items))
            elif etype == 'REGISTRY':
                summary_parts.append(self._summarize_registry(items))
            else:
                summary_parts.append(f"**{etype}**: {len(items)} items collected")
                
        return "\n\n".join(summary_parts)
        
    def _summarize_process_tree(self, items: List[Dict]) -> str:
        """Summarize process tree evidence"""
        if not items:
            return ""
            
        import json
        tree = json.loads(items[0]['content'])
        
        parts = ["**Process Tree:**"]
        
        # Parent process
        if tree.get('parent'):
            parent = tree['parent']
            parts.append(f"- Parent: {parent['name']} (PID {parent['pid']})")
            if parent.get('exe'):
                parts.append(f"  Path: {parent['exe']}")
            if parent.get('cmdline'):
                parts.append(f"  Command: {parent['cmdline']}")
        else:
            parts.append("- Parent: Unknown or terminated")
            
        # Child processes
        if tree.get('children'):
            parts.append(f"- Spawned {len(tree['children'])} child process(es):")
            for child in tree['children'][:5]:  # Limit to first 5
                parts.append(f"  - {child['name']} (PID {child['pid']})")
                if child.get('cmdline'):
                    parts.append(f"    Command: {child['cmdline']}")
        else:
            parts.append("- No child processes spawned")
                
        return "\n".join(parts)
        
    def _summarize_network(self, items: List[Dict]) -> str:
        """Summarize network evidence"""
        if not items:
            return ""
            
        import json
        net = json.loads(items[0]['content'])
        
        parts = ["**Network Activity:**"]
        
        conn_count = len(net.get('connections', []))
        listen_count = len(net.get('listening_ports', []))
        
        if conn_count > 0:
            parts.append(f"- {conn_count} active connection(s)")
            # Show all connections (up to 10)
            for conn in net['connections'][:10]:
                if conn.get('raddr'):
                    parts.append(f"  - Connected to {conn['raddr']} ({conn.get('status', 'UNKNOWN')})")
                elif conn.get('laddr'):
                    parts.append(f"  - Local: {conn['laddr']} ({conn.get('status', 'UNKNOWN')})")
        else:
            parts.append("- No active connections detected")
                    
        if listen_count > 0:
            parts.append(f"- Listening on {listen_count} port(s):")
            for port in net['listening_ports'][:5]:
                if port.get('laddr'):
                    parts.append(f"  - {port['laddr']}")
        else:
            parts.append("- No listening ports")
            
        return "\n".join(parts)
        
    def _summarize_filesystem(self, items: List[Dict]) -> str:
        """Summarize filesystem evidence"""
        if not items:
            return ""
            
        import json
        fs = json.loads(items[0]['content'])
        
        parts = ["**Filesystem Activity:**"]
        
        if fs.get('cwd'):
            parts.append(f"- Working directory: {fs['cwd']}")
        else:
            parts.append("- Working directory: Unknown")
            
        open_files = fs.get('open_files', [])
        if open_files:
            parts.append(f"- {len(open_files)} open file(s):")
            for f in open_files[:10]:  # Show up to 10 files
                parts.append(f"  - {f['path']}")
        else:
            parts.append("- No open files detected")
                
        return "\n".join(parts)
        
    def _summarize_registry(self, items: List[Dict]) -> str:
        """Summarize registry evidence"""
        if not items:
            return ""
            
        return f"**Registry Activity:** {len(items)} registry operations detected"
        
    def prioritize_evidence(self, evidence_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort evidence by importance"""
        importance_order = {'CRITICAL': 0, 'RELEVANT': 1, 'INCIDENTAL': 2}
        
        return sorted(
            evidence_items,
            key=lambda x: importance_order.get(x.get('importance', 'RELEVANT'), 1)
        )
