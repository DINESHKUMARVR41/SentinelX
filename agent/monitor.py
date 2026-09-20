"""
Process Monitor
Watches for new processes and triggers investigations
"""

import asyncio
import psutil
from datetime import datetime
from typing import Set, Optional
import logging

from agent.triggers import TriggerEngine

logger = logging.getLogger(__name__)


class ProcessMonitor:
    """Monitors system processes for suspicious behavior"""
    
    def __init__(self, orchestrator, config):
        self.orchestrator = orchestrator
        self.config = config
        self.trigger_engine = TriggerEngine(config.triggers if hasattr(config, 'triggers') else {})
        self.seen_pids: Set[int] = set()
        self.running = False
        self.monitor_task: Optional[asyncio.Task] = None
        
    async def start(self):
        """Start monitoring processes"""
        if self.running:
            return
            
        self.running = True
        logger.info("🔍 Process monitor started")
        
        # Initialize with current processes
        for proc in psutil.process_iter(['pid']):
            self.seen_pids.add(proc.pid)
            
        # Start monitoring loop
        self.monitor_task = asyncio.create_task(self._monitor_loop())
        
    async def stop(self):
        """Stop monitoring"""
        self.running = False
        if self.monitor_task:
            self.monitor_task.cancel()
            try:
                await self.monitor_task
            except asyncio.CancelledError:
                pass
        logger.info("Process monitor stopped")
        
    def is_running(self) -> bool:
        """Check if monitor is running"""
        return self.running
        
    async def _monitor_loop(self):
        """Main monitoring loop"""
        while self.running:
            try:
                # Check for new processes
                current_pids = set()
                for proc in psutil.process_iter(['pid']):
                    current_pids.add(proc.pid)
                    
                # Find new processes
                new_pids = current_pids - self.seen_pids
                
                for pid in new_pids:
                    try:
                        proc = psutil.Process(pid)
                        await self._evaluate_process(proc)
                    except psutil.NoSuchProcess:
                        continue
                    except Exception as e:
                        logger.error(f"Error evaluating PID {pid}: {e}")
                        
                self.seen_pids = current_pids
                
                # Sleep before next check
                await asyncio.sleep(2)  # Check every 2 seconds
                
            except Exception as e:
                logger.error(f"Monitor loop error: {e}", exc_info=True)
                await asyncio.sleep(5)
                
    async def _evaluate_process(self, proc: psutil.Process):
        """Evaluate if process should trigger investigation"""
        try:
            should_investigate, reasons = self.trigger_engine.should_investigate(proc)
            
            if should_investigate:
                logger.info(f"🚨 Suspicious process detected: PID {proc.pid} ({proc.name()})")
                for reason in reasons:
                    logger.info(f"  - {reason}")
                    
                # Gather initial process info
                try:
                    parent = proc.parent()
                    parent_pid = parent.pid if parent else None
                    parent_name = parent.name() if parent else None
                except:
                    parent_pid = None
                    parent_name = None
                    
                try:
                    proc_path = proc.exe()
                    cmdline = ' '.join(proc.cmdline())
                    username = proc.username()
                except (psutil.AccessDenied, psutil.NoSuchProcess):
                    proc_path = None
                    cmdline = None
                    username = None
                    
                # Trigger investigation
                await self.orchestrator.trigger_investigation({
                    'pid': proc.pid,
                    'process_name': proc.name(),
                    'process_path': proc_path,
                    'parent_pid': parent_pid,
                    'parent_name': parent_name,
                    'command_line': cmdline,
                    'user_name': username,
                    'trigger_reasons': reasons,
                    'triggered_at': datetime.utcnow().isoformat()
                })
                
        except psutil.NoSuchProcess:
            pass
        except Exception as e:
            logger.error(f"Error evaluating process {proc.pid}: {e}")
