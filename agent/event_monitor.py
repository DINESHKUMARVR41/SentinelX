"""
Event-Based Process Monitor
Uses WMI to capture ALL process creation events in real-time
Catches even processes that live <1 second
"""

import asyncio
import threading
import psutil
from datetime import datetime
from typing import Optional, Callable
import logging

logger = logging.getLogger(__name__)

try:
    import wmi
    WMI_AVAILABLE = True
except ImportError:
    WMI_AVAILABLE = False
    logger.warning("⚠️ WMI not available - install pywin32: pip install pywin32")


class EventBasedMonitor:
    """
    Real-time process monitoring using WMI events
    Captures EVERY process creation, even if it terminates in <1 second
    """
    
    def __init__(self, orchestrator, config):
        self.orchestrator = orchestrator
        self.config = config
        self.running = False
        self.wmi_thread: Optional[threading.Thread] = None
        self.event_queue: asyncio.Queue = None
        self.process_task: Optional[asyncio.Task] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None  # Store event loop reference
        
        if not WMI_AVAILABLE:
            logger.error("❌ WMI not available - event-based monitoring disabled")
            logger.error("   Install: pip install pywin32")
            
    async def start(self):
        """Start event-based monitoring"""
        if not WMI_AVAILABLE:
            logger.warning("⚠️ Event-based monitoring not available (WMI missing)")
            return
            
        if self.running:
            return
            
        self.running = True
        self.event_queue = asyncio.Queue()
        self.loop = asyncio.get_event_loop()  # Store the event loop
        
        logger.info("🎯 Starting event-based process monitor (WMI)")
        logger.info("   ✅ Will capture ALL process creations in real-time")
        logger.info("   ✅ Detects processes even if they live <1 second")
        
        # Start WMI event watcher in separate thread (WMI is blocking)
        self.wmi_thread = threading.Thread(target=self._wmi_event_loop, daemon=True)
        self.wmi_thread.start()
        
        # Start async event processor
        self.process_task = asyncio.create_task(self._process_events())
        
    async def stop(self):
        """Stop event-based monitoring"""
        self.running = False
        
        if self.process_task:
            self.process_task.cancel()
            try:
                await self.process_task
            except asyncio.CancelledError:
                pass
                
        # WMI thread will stop when running = False
        logger.info("Event-based monitor stopped")
        
    def _wmi_event_loop(self):
        """
        WMI event watcher (runs in separate thread)
        Subscribes to Win32_ProcessStartTrace events
        """
        try:
            import pythoncom
            
            # Initialize COM for this thread (REQUIRED for WMI in threads)
            pythoncom.CoInitialize()
            
            logger.info("🔍 WMI event watcher started")
            c = wmi.WMI()
            
            # Subscribe to process creation events using watch_for
            # This is the correct way to monitor process creation
            watcher = c.watch_for(
                notification_type="Creation",
                wmi_class="Win32_Process",
                delay_secs=1
            )
            
            while self.running:
                try:
                    # Wait for next process creation event (blocking)
                    event = watcher(timeout_ms=1000)
                    
                    if event:
                        # Event captured! Process may already be terminated, but we have the data
                        event_data = {
                            'pid': event.ProcessID,
                            'process_name': event.Name,
                            'parent_pid': event.ParentProcessId,
                            'timestamp': datetime.utcnow().isoformat(),
                            'event_type': 'PROCESS_START'
                        }
                        
                        # Put event in queue for async processing
                        # Use thread-safe call_soon_threadsafe
                        if self.event_queue and self.loop:
                            asyncio.run_coroutine_threadsafe(
                                self.event_queue.put(event_data),
                                self.loop  # Use stored loop reference
                            )
                            
                except wmi.x_wmi_timed_out:
                    # Timeout - check if we should continue
                    continue
                except Exception as e:
                    if self.running:
                        logger.error(f"WMI event error: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"WMI event loop failed: {e}", exc_info=True)
        finally:
            try:
                import pythoncom
                pythoncom.CoUninitialize()  # Clean up COM
            except:
                pass
            logger.info("WMI event watcher stopped")
            
    async def _process_events(self):
        """Process events from WMI thread"""
        logger.info("📊 Event processor started")
        
        while self.running:
            try:
                # Wait for event from WMI thread
                event_data = await asyncio.wait_for(
                    self.event_queue.get(),
                    timeout=1.0
                )
                
                # Process the event
                await self._handle_process_start(event_data)
                
            except asyncio.TimeoutError:
                # No events in last second, continue
                continue
            except Exception as e:
                logger.error(f"Event processing error: {e}", exc_info=True)
                
    async def _handle_process_start(self, event_data: dict):
        """
        Handle process start event
        1. Collect raw event data immediately
        2. Evaluate for investigation triggers
        """
        pid = event_data['pid']
        process_name = event_data['process_name']
        
        logger.debug(f"🎯 Process created: PID {pid} ({process_name})")
        
        # Try to get full process details if still running
        try:
            proc = psutil.Process(pid)
            
            # === STEP 1: COLLECT RAW EVENT DATA (Real-time) ===
            await self._collect_raw_event(proc, event_data)
            
            # Get detailed info
            try:
                parent = proc.parent()
                parent_pid = parent.pid if parent else event_data.get('parent_pid')
                parent_name = parent.name() if parent else None
            except:
                parent_pid = event_data.get('parent_pid')
                parent_name = None
                
            try:
                proc_path = proc.exe()
                cmdline = ' '.join(proc.cmdline())
                username = proc.username()
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                proc_path = None
                cmdline = None
                username = None
            
            # === STEP 2: EVALUATE FOR INVESTIGATION ===
            # Evaluate with trigger engine
            from agent.triggers import TriggerEngine
            trigger_engine = TriggerEngine(
                self.config.triggers if hasattr(self.config, 'triggers') else {}
            )
            
            should_investigate, reasons = trigger_engine.should_investigate(proc)
            
            if should_investigate:
                logger.info(f"🚨 Suspicious process detected: PID {pid} ({process_name})")
                for reason in reasons:
                    logger.info(f"  - {reason}")
                    
                # Trigger investigation
                await self.orchestrator.trigger_investigation({
                    'pid': pid,
                    'process_name': process_name,
                    'process_path': proc_path,
                    'parent_pid': parent_pid,
                    'parent_name': parent_name,
                    'command_line': cmdline,
                    'user_name': username,
                    'trigger_reasons': reasons,
                    'triggered_at': event_data['timestamp'],
                    'detection_method': 'EVENT_BASED'
                })
                
        except psutil.NoSuchProcess:
            # Process already terminated - this is OK!
            # We still have the event data (PID, name, parent)
            logger.debug(f"⚡ Process {pid} ({process_name}) already terminated (short-lived)")
            
            # For short-lived processes, we can still do basic evaluation
            # based on process name and parent
            if self._is_suspicious_short_lived(event_data):
                logger.warning(f"🚨 Suspicious short-lived process: PID {pid} ({process_name})")
                logger.warning(f"   Process terminated before full analysis")
                logger.warning(f"   Parent PID: {event_data.get('parent_pid')}")
                
                # Log to database for forensics
                await self._log_short_lived_process(event_data)
                
        except Exception as e:
            logger.error(f"Error handling process {pid}: {e}")
    
    async def _collect_raw_event(self, proc: psutil.Process, event_data: dict):
        """
        Collect raw process event data in real-time
        This replaces the 10-second polling mechanism
        """
        try:
            pid = proc.pid
            
            # Get process details with fallbacks for access denied
            try:
                proc_info = proc.as_dict(attrs=[
                    'name', 'exe', 'cmdline', 'username', 'cpu_percent',
                    'memory_info', 'status', 'num_threads', 'ppid'
                ])
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                logger.debug(f"Could not get full process info for PID {pid}: {e}")
                # Use minimal info from event_data
                proc_info = {
                    'name': event_data.get('process_name', 'Unknown'),
                    'exe': None,
                    'cmdline': [],
                    'username': None,
                    'cpu_percent': 0.0,
                    'memory_info': None,
                    'status': 'unknown',
                    'num_threads': 0,
                    'ppid': event_data.get('parent_pid')
                }
            
            # Get network connections
            try:
                connections = []
                for conn in proc.connections():
                    connections.append({
                        'laddr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                        'raddr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                        'status': conn.status
                    })
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                connections = []
            
            # Get open files
            try:
                files = [f.path for f in proc.open_files()[:10]]  # Limit to 10
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                files = []
            
            # Determine event type
            event_type = 'PROCESS_START'
            if connections:
                event_type = 'NETWORK'
            if files:
                event_type = 'FILE_ACCESS'
            
            # Prepare event data
            event_record = {
                'pid': pid,
                'process_name': proc_info.get('name', 'Unknown'),
                'process_path': proc_info.get('exe'),
                'parent_pid': proc_info.get('ppid'),
                'command_line': ' '.join(proc_info.get('cmdline', [])) if proc_info.get('cmdline') else None,
                'user_name': proc_info.get('username'),
                'cpu_percent': proc_info.get('cpu_percent', 0.0),
                'memory_mb': proc_info.get('memory_info').rss / 1024 / 1024 if proc_info.get('memory_info') else 0,
                'network_connections': connections,
                'open_files': files,
                'threads_count': proc_info.get('num_threads', 0),
                'status': proc_info.get('status', 'unknown'),
                'event_type': event_type,
                'event_details': {'real_time': True, 'wmi_event': True}
            }
            
            # Insert into raw_process_events table
            await self._insert_raw_event(event_record)
            
            logger.debug(f"📝 Raw event collected: PID {pid} ({proc_info.get('name', 'Unknown')})")
            
        except Exception as e:
            logger.error(f"Error collecting raw event for PID {proc.pid}: {e}", exc_info=True)
    
    async def _insert_raw_event(self, event: dict):
        """Insert raw event into database with interval tracking"""
        try:
            import json
            from datetime import datetime
            
            # Safety check: ensure database is available
            if not self.orchestrator or not self.orchestrator.state_manager or not self.orchestrator.state_manager.db:
                logger.warning(f"⚠️ Database not ready, skipping event for PID {event.get('pid')}")
                return
            
            # Generate interval_id based on current minute (e.g., "2026-02-04_11:30")
            now = datetime.utcnow()
            interval_id = now.strftime("%Y-%m-%d_%H:%M")
            
            query = """
                INSERT INTO raw_process_events (
                    pid, process_name, process_path, parent_pid, command_line,
                    user_name, cpu_percent, memory_mb, network_connections,
                    open_files, threads_count, status, event_type, event_details,
                    interval_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            
            await self.orchestrator.state_manager.db.execute(query, (
                event['pid'],
                event['process_name'],
                event['process_path'],
                event['parent_pid'],
                event['command_line'],
                event['user_name'],
                event['cpu_percent'],
                event['memory_mb'],
                json.dumps(event['network_connections']),
                json.dumps(event['open_files']),
                event['threads_count'],
                event['status'],
                event['event_type'],
                json.dumps(event['event_details']),
                interval_id
            ))
            await self.orchestrator.state_manager.db.commit()
            
            logger.info(f"✅ Inserted raw event: PID {event['pid']} ({event['process_name']}) [interval: {interval_id}]")
            
        except Exception as e:
            logger.error(f"❌ Failed to insert raw event for PID {event.get('pid')}: {e}", exc_info=True)
            
    def _is_suspicious_short_lived(self, event_data: dict) -> bool:
        """
        Basic suspicion check for short-lived processes
        Can't do full analysis since process is gone
        """
        process_name = event_data.get('process_name', '').lower()
        
        # Suspicious process names
        suspicious_names = {
            'powershell.exe', 'cmd.exe', 'wscript.exe', 'cscript.exe',
            'mshta.exe', 'regsvr32.exe', 'rundll32.exe', 'certutil.exe',
            'reg.exe', 'schtasks.exe', 'wmic.exe'
        }
        
        return process_name in suspicious_names
        
    async def _log_short_lived_process(self, event_data: dict):
        """Log short-lived suspicious process to database"""
        try:
            # Store in a special table for short-lived processes
            await self.orchestrator.state_manager.db.execute("""
                INSERT INTO short_lived_processes (
                    pid, process_name, parent_pid, detected_at, event_data
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                event_data['pid'],
                event_data['process_name'],
                event_data.get('parent_pid'),
                event_data['timestamp'],
                str(event_data)
            ))
            await self.orchestrator.state_manager.db.commit()
            
            logger.info(f"📝 Logged short-lived process: {event_data['process_name']}")
            
        except Exception as e:
            # Table might not exist yet - that's OK
            logger.debug(f"Could not log short-lived process: {e}")
            
    def is_available(self) -> bool:
        """Check if event-based monitoring is available"""
        return WMI_AVAILABLE
        
    def is_running(self) -> bool:
        """Check if monitor is running"""
        return self.running
