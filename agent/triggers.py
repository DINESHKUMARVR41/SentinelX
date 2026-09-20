"""
Process Trigger Detection
Defines what makes a process suspicious and worthy of investigation

BEHAVIOR-BASED DETECTION:
- Analyzes process behavior regardless of location
- Focuses on suspicious actions, not just file paths
- Comprehensive system-wide monitoring
"""

import psutil
import re
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
import logging

logger = logging.getLogger(__name__)


class TriggerEngine:
    """Evaluates if a process should trigger investigation based on behavior"""
    
    # Suspicious parent-child combinations (behavior-based)
    SUSPICIOUS_SPAWNS = {
        'chrome.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'regsvr32.exe'],
        'firefox.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'regsvr32.exe'],
        'msedge.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'regsvr32.exe'],
        'iexplore.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe'],
        'winword.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'regsvr32.exe'],
        'excel.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe', 'mshta.exe', 'regsvr32.exe'],
        'powerpnt.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe'],
        'outlook.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe'],
        'acrord32.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe'],
        'acrobat.exe': ['powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe'],
    }
    
    # Suspicious directories (still useful as one indicator)
    SUSPICIOUS_PATHS = [
        'temp', 'tmp', 'downloads', 'appdata\\local\\temp', 'programdata',
        'public', 'recycler', 'recycle.bin', '$recycle.bin', 'perflogs'
    ]
    
    # Suspicious command line patterns (MITRE ATT&CK based)
    SUSPICIOUS_CMDLINE_PATTERNS = [
        # PowerShell obfuscation/evasion
        (r'-enc(oded)?command', 'Encoded PowerShell command'),
        (r'-nop(rofile)?', 'PowerShell no profile'),
        (r'-w(indowstyle)?\s+hidden', 'Hidden window'),
        (r'-ep\s+bypass', 'Execution policy bypass'),
        (r'-executionpolicy\s+bypass', 'Execution policy bypass'),
        
        # Download/execution patterns
        (r'invoke-expression', 'Invoke-Expression (code execution)'),
        (r'\biex\s*\(', 'IEX shorthand (code execution)'),
        (r'downloadstring', 'Web download'),
        (r'downloadfile', 'File download'),
        (r'webclient', 'Web client usage'),
        (r'net\.webclient', 'WebClient object'),
        (r'bitstransfer', 'BITS transfer'),
        (r'start-bitstransfer', 'BITS download'),
        
        # System manipulation
        (r'invoke-wmimethod', 'WMI method invocation'),
        (r'invoke-cimmethod', 'CIM method invocation'),
        (r'get-wmiobject', 'WMI object query'),
        (r'register-scheduledtask', 'Scheduled task creation'),
        (r'new-service', 'Service creation'),
        (r'set-service', 'Service modification'),
        
        # Credential access
        (r'mimikatz', 'Credential dumping tool'),
        (r'invoke-mimikatz', 'Mimikatz execution'),
        (r'sekurlsa', 'LSASS credential access'),
        (r'lsadump', 'LSA secrets dump'),
        (r'procdump.*lsass', 'LSASS memory dump'),
        
        # Persistence
        (r'new-itemproperty.*currentversion\\run', 'Registry run key'),
        (r'set-itemproperty.*currentversion\\run', 'Registry run key modification'),
        (r'schtasks\s+/create', 'Scheduled task creation'),
        (r'reg\s+add.*\\run', 'Registry persistence'),
        
        # Defense evasion
        (r'set-mppreference\s+-disablerealtimemonitoring', 'Disable Windows Defender'),
        (r'add-mppreference\s+-exclusion', 'Add Defender exclusion'),
        (r'stop-service.*windefend', 'Stop Defender service'),
        (r'uninstall-windowsfeature.*defender', 'Uninstall Defender'),
        
        # Lateral movement
        (r'invoke-command\s+-computername', 'Remote command execution'),
        (r'enter-pssession', 'Remote PowerShell session'),
        (r'new-pssession', 'New remote session'),
        (r'\\\\[^\\]+\\[a-z]\$', 'Admin share access'),
        
        # Discovery
        (r'get-aduser', 'AD user enumeration'),
        (r'get-adcomputer', 'AD computer enumeration'),
        (r'net\s+(user|group|localgroup)', 'User/group enumeration'),
        (r'nltest\s+/dclist', 'Domain controller discovery'),
        
        # Certutil abuse
        (r'certutil.*-decode', 'Certutil decode (file obfuscation)'),
        (r'certutil.*-urlcache', 'Certutil download'),
        
        # LOLBins (Living Off the Land Binaries)
        (r'regsvr32.*scrobj\.dll', 'Regsvr32 script execution'),
        (r'mshta\s+http', 'MSHTA remote execution'),
        (r'rundll32.*javascript:', 'Rundll32 JavaScript'),
        (r'wmic\s+process\s+call\s+create', 'WMIC process creation'),
    ]
    
    # Processes that commonly indicate malicious activity
    SUSPICIOUS_PROCESS_NAMES = {
        'mshta.exe', 'regsvr32.exe', 'rundll32.exe', 'wmic.exe',
        'cscript.exe', 'wscript.exe', 'msiexec.exe', 'regasm.exe',
        'regsvcs.exe', 'installutil.exe', 'certutil.exe'
    }
    
    # System processes that should never be investigated
    SYSTEM_PROCESS_WHITELIST = {
        'system', 'smss.exe', 'csrss.exe', 'wininit.exe', 'services.exe',
        'lsass.exe', 'winlogon.exe', 'dwm.exe', 'fontdrvhost.exe',
        'conhost.exe', 'sihost.exe', 'taskhostw.exe', 'runtimebroker.exe',
        'searchindexer.exe', 'searchhost.exe', 'startmenuexperiencehost.exe',
        'shellexperiencehost.exe', 'textinputhost.exe', 'securityhealthservice.exe'
    }
    
    # Trusted paths (reduce false positives)
    TRUSTED_PATHS = [
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.compiled_patterns = [
            (re.compile(pattern, re.IGNORECASE), desc)
            for pattern, desc in self.SUSPICIOUS_CMDLINE_PATTERNS
        ]
        
    def should_investigate(self, proc: psutil.Process) -> tuple[bool, List[str]]:
        """
        Determine if process should trigger investigation based on BEHAVIOR
        Returns: (should_investigate, reasons)
        
        BEHAVIOR-BASED DETECTION:
        - Analyzes what the process is DOING, not just where it's located
        - Checks command line patterns, parent-child relationships, network activity
        - Works system-wide, not limited to specific directories
        """
        reasons = []
        suspicion_score = 0  # Track cumulative suspicion
        
        try:
            proc_name = proc.name().lower()
            
            # Skip system processes
            if proc_name in self.SYSTEM_PROCESS_WHITELIST:
                return False, []
                
            # Get process details
            try:
                proc_path = proc.exe()
                cmdline = ' '.join(proc.cmdline()) if proc.cmdline() else ''
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                proc_path = None
                cmdline = ''
            
            # === BEHAVIOR CHECK 1: Command Line Analysis (HIGHEST PRIORITY) ===
            if cmdline and self.config.get('suspicious_cmdline', True):
                for pattern, description in self.compiled_patterns:
                    if pattern.search(cmdline):
                        reasons.append(f"Suspicious command: {description}")
                        suspicion_score += 3  # High weight
            
            # === BEHAVIOR CHECK 2: Suspicious Parent-Child Relationship ===
            if self.config.get('browser_spawns_shell', True):
                try:
                    parent = proc.parent()
                    if parent:
                        parent_name = parent.name().lower()
                        if parent_name in self.SUSPICIOUS_SPAWNS:
                            if proc_name in self.SUSPICIOUS_SPAWNS[parent_name]:
                                reasons.append(f"Suspicious spawn: {parent_name} → {proc_name}")
                                suspicion_score += 2
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # === BEHAVIOR CHECK 3: Suspicious Process Names (LOLBins) ===
            if proc_name in self.SUSPICIOUS_PROCESS_NAMES:
                # Check if running from trusted location
                is_trusted = False
                if proc_path:
                    proc_path_lower = proc_path.lower()
                    for trusted in self.TRUSTED_PATHS:
                        if proc_path_lower.startswith(trusted):
                            is_trusted = True
                            break
                
                if not is_trusted:
                    reasons.append(f"Suspicious process: {proc_name} from untrusted location")
                    suspicion_score += 2
                elif cmdline:  # Even from trusted location, check command line
                    reasons.append(f"LOLBin execution: {proc_name} (check command line)")
                    suspicion_score += 1
            
            # === BEHAVIOR CHECK 4: Network Activity ===
            if self.config.get('rapid_network_activity', True):
                try:
                    connections = proc.connections()
                    if len(connections) > 5:
                        # Higher score if from untrusted location
                        is_trusted = False
                        if proc_path:
                            proc_path_lower = proc_path.lower()
                            is_trusted = any(proc_path_lower.startswith(trusted) for trusted in self.TRUSTED_PATHS)
                        
                        if is_trusted:
                            reasons.append(f"High network activity: {len(connections)} connections")
                            suspicion_score += 1
                        else:
                            reasons.append(f"High network activity from untrusted location: {len(connections)} connections")
                            suspicion_score += 2
                    
                    # Check for external connections
                    external_ips = []
                    for conn in connections:
                        if hasattr(conn, 'raddr') and conn.raddr and hasattr(conn.raddr, 'ip'):
                            ip = conn.raddr.ip
                            # Skip local/private IPs
                            if not (ip.startswith('127.') or ip.startswith('192.168.') or 
                                   ip.startswith('10.') or ip.startswith('172.')):
                                external_ips.append(ip)
                    
                    if len(external_ips) > 2:
                        reasons.append(f"Multiple external connections: {len(external_ips)} IPs")
                        suspicion_score += 1
                        
                except (psutil.AccessDenied, psutil.NoSuchProcess, AttributeError):
                    pass
            
            # === BEHAVIOR CHECK 5: Unusual Process Characteristics ===
            try:
                # Check if process has no window (hidden)
                if hasattr(proc, 'num_threads'):
                    threads = proc.num_threads()
                    if threads > 50:
                        reasons.append(f"High thread count: {threads} threads")
                        suspicion_score += 1
                
                # Check memory usage
                mem_info = proc.memory_info()
                if mem_info.rss > 500 * 1024 * 1024:  # > 500MB
                    reasons.append(f"High memory usage: {mem_info.rss // (1024*1024)}MB")
                    suspicion_score += 1
                    
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                pass
            
            # === BEHAVIOR CHECK 6: Spawned from Suspicious Directory (Lower Priority) ===
            if proc_path and self.config.get('temp_spawn', True):
                proc_path_lower = proc_path.lower()
                
                # Check if NOT in trusted paths
                is_trusted = any(proc_path_lower.startswith(trusted) for trusted in self.TRUSTED_PATHS)
                
                if not is_trusted:
                    for suspicious_dir in self.SUSPICIOUS_PATHS:
                        if suspicious_dir in proc_path_lower:
                            reasons.append(f"Spawned from suspicious directory: {suspicious_dir}")
                            suspicion_score += 1
                            break
            
            # === BEHAVIOR CHECK 7: Unsigned or Suspicious Executable ===
            if proc_path and self.config.get('unsigned_executable', True):
                # Check file extension
                if proc_path.lower().endswith(('.tmp', '.dat', '.bin', '.txt')):
                    reasons.append(f"Suspicious file extension: {Path(proc_path).suffix}")
                    suspicion_score += 2
            
            # === DECISION: Investigate if suspicion score is high enough ===
            # Score >= 2: Investigate (at least one strong indicator or multiple weak ones)
            should_investigate = suspicion_score >= 2 or len(reasons) >= 2
            
            if should_investigate:
                reasons.append(f"[Suspicion Score: {suspicion_score}]")
                        
            return should_investigate, reasons
            
        except psutil.NoSuchProcess:
            return False, []
        except Exception as e:
            logger.error(f"Error evaluating trigger for PID {proc.pid}: {e}")
            return False, []
    
    def get_trigger_summary(self) -> Dict[str, Any]:
        """Get summary of trigger configuration"""
        return {
            'behavior_based': True,
            'system_wide': True,
            'suspicious_spawns': len(self.SUSPICIOUS_SPAWNS),
            'cmdline_patterns': len(self.SUSPICIOUS_CMDLINE_PATTERNS),
            'suspicious_processes': len(self.SUSPICIOUS_PROCESS_NAMES),
            'config': self.config
        }
