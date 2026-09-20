"""
PROCSee Agent Main Entry Point
Manages agent lifecycle, initialization, and coordination
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path
from typing import Optional

from agent.state_manager import StateManager
from agent.monitor import ProcessMonitor
from agent.event_monitor import EventBasedMonitor
from agent.orchestrator import InvestigationOrchestrator
from agent.config import load_config
from agent.interval_collector import IntervalCollector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PROCSeeAgent:
    """Main agent coordinator"""
    
    def __init__(self):
        self.config = load_config()
        self.state_manager: Optional[StateManager] = None
        self.monitor: Optional[ProcessMonitor] = None
        self.event_monitor: Optional[EventBasedMonitor] = None
        self.orchestrator: Optional[InvestigationOrchestrator] = None
        self.interval_collector: Optional[IntervalCollector] = None
        self.running = False
        
    async def initialize(self):
        """Initialize all agent components"""
        logger.info("🚀 Initializing PROCSee Agent...")
        
        try:
            # Initialize state manager (database)
            self.state_manager = StateManager(self.config.database_path)
            await asyncio.wait_for(self.state_manager.initialize(), timeout=10.0)
            logger.info("✓ State manager initialized")
            
            # Initialize orchestrator
            self.orchestrator = InvestigationOrchestrator(
                self.state_manager,
                self.config
            )
            logger.info("✓ Investigation orchestrator initialized")
            
            # Resume incomplete investigations (with timeout to prevent hanging)
            try:
                await asyncio.wait_for(
                    self.orchestrator.resume_incomplete_investigations(), 
                    timeout=5.0
                )
            except asyncio.TimeoutError:
                logger.warning("Resume incomplete investigations timed out - skipping")
            
            # Initialize process monitor (polling-based, 2-second intervals)
            self.monitor = ProcessMonitor(
                self.orchestrator,
                self.config
            )
            logger.info("✓ Process monitor initialized")
            
            # Initialize event-based monitor (real-time, catches all processes)
            self.event_monitor = EventBasedMonitor(
                self.orchestrator,
                self.config
            )
            if self.event_monitor.is_available():
                logger.info("✓ Event-based monitor initialized (WMI)")
            else:
                logger.warning("⚠️ Event-based monitor unavailable (install pywin32)")
            
            # Initialize interval collector (autonomous querying system)
            self.interval_collector = IntervalCollector(
                self.state_manager,
                self.config
            )
            logger.info("✓ Interval collector initialized")
            
            logger.info("✅ PROCSee Agent ready")
        except Exception as e:
            logger.error(f"Failed to initialize agent: {e}", exc_info=True)
            raise
        
    async def start(self, standalone=False):
        """Start the agent (non-blocking by default, blocking if standalone)"""
        if self.running:
            logger.warning("Agent already running")
            return
            
        self.running = True
        logger.info("▶️  Starting PROCSee Agent...")
        
        try:
            # Log system event
            await self.state_manager.log_system_event(
                "AGENT_START",
                "PROCSee agent started"
            )
            
            if not self.config.live_ai_enabled or not self.config.enable_live_monitoring:
                logger.warning(
                    "DEMO MODE: live Windows monitoring is disabled. Set ENABLE_LIVE_MONITORING=true "
                    "to opt in. The dashboard live-AI explanation remains available and makes only explicit requests."
                )
                return

            # Start event-based monitoring (real-time, catches all processes)
            if self.event_monitor and self.event_monitor.is_available():
                await self.event_monitor.start()
                logger.info("✅ Event-based monitoring active (real-time process detection)")
                logger.info("   ✅ Replaces 2-second polling monitor")
                logger.info("   ✅ Feeds real-time data to raw_process_events table")
            else:
                logger.warning("⚠️ Event-based monitoring not available")
                logger.warning("   Falling back to polling-based monitor (may miss short-lived processes)")
                # Start polling-based monitoring as fallback
                await self.monitor.start()
            
            # Start interval collection (1-minute summaries from real-time data)
            await self.interval_collector.start()
            
            # Start interval analysis loop as background task
            asyncio.create_task(self._interval_analysis_loop())
            
            logger.info("✅ Agent started successfully")
            
            # If standalone mode, keep running until stopped
            if standalone:
                try:
                    while self.running:
                        await asyncio.sleep(1)
                except asyncio.CancelledError:
                    logger.info("Agent cancelled")
        except Exception as e:
            logger.error(f"Failed to start agent: {e}", exc_info=True)
            self.running = False
            raise
    
    async def _interval_analysis_loop(self):
        """Periodically analyze interval summaries"""
        while self.running:
            try:
                await asyncio.sleep(60)  # Check every minute
                # Run analysis as a task so it doesn't block the loop
                asyncio.create_task(self.orchestrator.analyze_latest_interval())
            except Exception as e:
                logger.error(f"Interval analysis error: {e}", exc_info=True)
            
    async def stop(self):
        """Stop the agent gracefully"""
        if not self.running:
            return
            
        logger.info("⏹️  Stopping PROCSee Agent...")
        self.running = False
        
        # Stop event monitor
        if self.event_monitor:
            await self.event_monitor.stop()
        
        # Stop polling monitor
        if self.monitor:
            await self.monitor.stop()
        
        # Stop interval collector
        if self.interval_collector:
            await self.interval_collector.stop()
            
        # Stop orchestrator
        if self.orchestrator:
            await self.orchestrator.stop()
            
        # Log system event
        if self.state_manager:
            await self.state_manager.log_system_event(
                "AGENT_STOP",
                "PROCSee agent stopped"
            )
            await self.state_manager.close()
            
        logger.info("✅ PROCSee Agent stopped")
        
    async def health_check(self) -> dict:
        """Get agent health status"""
        return {
            "running": self.running,
            "active_investigations": await self.orchestrator.get_active_count() if self.orchestrator else 0,
            "event_monitor_status": self.event_monitor.is_running() if self.event_monitor else False,
            "polling_monitor_status": self.monitor.is_running() if self.monitor else False,
            "interval_collector_status": self.interval_collector.running if self.interval_collector else False
        }


# Global agent instance
agent: Optional[PROCSeeAgent] = None


async def main():
    """Main entry point"""
    global agent
    
    # Handle command line arguments
    if len(sys.argv) > 1 and sys.argv[1] == "--init-db":
        logger.info("Initializing database...")
        from agent.state_manager import init_database
        await init_database()
        logger.info("✅ Database initialized")
        return
    
    agent = PROCSeeAgent()
    
    try:
        await agent.initialize()
        await agent.start(standalone=True)  # Run in standalone mode (blocking)
    except KeyboardInterrupt:
        logger.info("Keyboard interrupt received")
    except Exception as e:
        logger.error(f"Agent error: {e}", exc_info=True)
    finally:
        if agent:
            await agent.stop()


if __name__ == "__main__":
    asyncio.run(main())
