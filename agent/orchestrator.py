"""
Investigation Orchestrator
Manages investigation lifecycle and phase transitions
"""

import asyncio
import uuid
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
import logging

from agent.state_manager import StateManager
from agent.collector import ForensicCollector
from agent.gemini_client import GeminiClient
from agent.evidence_processor import EvidenceProcessor
from agent.query_handler import QueryHandler

logger = logging.getLogger(__name__)


class InvestigationOrchestrator:
    """Orchestrates investigation lifecycle"""
    
    PHASES = [
        'TRIGGERED',
        'COLLECTING',
        'ANALYZING',
        'DEEP_INVESTIGATION',
        'MONITORING',
        'COMPLETED'
    ]
    
    def __init__(self, state_manager: StateManager, config):
        self.state_manager = state_manager
        self.config = config
        self.collector = ForensicCollector(state_manager, config)
        self.query_handler = QueryHandler(state_manager)
        self.gemini_client = GeminiClient(config, self.query_handler)
        self.evidence_processor = EvidenceProcessor()
        self.active_investigations: Dict[str, asyncio.Task] = {}
        
    async def trigger_investigation(self, process_data: Dict[str, Any]):
        """Trigger new investigation"""
        # Generate investigation ID
        inv_id = f"inv_{uuid.uuid4().hex[:12]}"
        process_data['id'] = inv_id
        
        # Create investigation record
        await self.state_manager.create_investigation(process_data)
        
        logger.info(f"🔍 Investigation triggered: {inv_id} (PID {process_data['pid']})")
        
        # Start investigation task
        if self.config.auto_investigate:
            task = asyncio.create_task(self._run_investigation(inv_id))
            self.active_investigations[inv_id] = task
        
        return inv_id
        
    async def _run_investigation(self, inv_id: str):
        """Run investigation through all phases"""
        try:
            logger.info(f"Starting investigation: {inv_id}")
            
            # Get investigation data
            inv = await self.state_manager.get_investigation(inv_id)
            if not inv:
                logger.error(f"Investigation {inv_id} not found")
                return
                
            # Phase 1: COLLECTING
            await self._phase_collecting(inv_id, inv)
            
            # Phase 2: ANALYZING
            await self._phase_analyzing(inv_id, inv)
            
            # Phase 3: DEEP_INVESTIGATION (conditional)
            analysis = await self.state_manager.get_investigation(inv_id)
            if analysis and analysis.get('risk_score', 0) > 0.6:
                await self._phase_deep_investigation(inv_id, inv)
                
            # Phase 4: MONITORING
            await self._phase_monitoring(inv_id, inv)
            
            # Phase 5: COMPLETED
            await self._phase_completed(inv_id)
            
        except Exception as e:
            logger.error(f"Investigation {inv_id} error: {e}", exc_info=True)
            await self.state_manager.update_investigation(inv_id, {
                'status': 'COMPLETED',
                'error_message': str(e),
                'completed_at': datetime.utcnow().isoformat()
            })
        finally:
            if inv_id in self.active_investigations:
                del self.active_investigations[inv_id]
        
    async def _phase_collecting(self, inv_id: str, inv: Dict):
        """Phase 1: Collect evidence"""
        logger.info(f"[{inv_id}] Phase: COLLECTING")
        
        await self.state_manager.update_investigation(inv_id, {
            'status': 'COLLECTING',
            'current_phase': 'COLLECTING',
            'started_at': datetime.utcnow().isoformat()
        })
        
        # Create checkpoint
        await self.state_manager.create_snapshot(inv_id, 'COLLECTING', {
            'phase': 'COLLECTING',
            'started_at': datetime.utcnow().isoformat()
        })
        
        pid = inv['pid']
        
        # Collect evidence
        await self.collector.collect_process_tree(pid, inv_id)
        await asyncio.sleep(0.5)
        
        await self.collector.collect_network_connections(pid, inv_id)
        await asyncio.sleep(0.5)
        
        await self.collector.collect_filesystem_activity(pid, inv_id)
        
        logger.info(f"[{inv_id}] Evidence collection complete")
        
    async def _phase_analyzing(self, inv_id: str, inv: Dict):
        """Phase 2: Gemini analysis"""
        logger.info(f"[{inv_id}] Phase: ANALYZING")
        
        await self.state_manager.update_investigation(inv_id, {
            'status': 'ANALYZING',
            'current_phase': 'ANALYZING'
        })
        
        # Get all evidence
        evidence_items = await self.state_manager.get_evidence(inv_id)
        
        # Summarize evidence
        evidence_summary = self.evidence_processor.summarize_evidence(evidence_items)
        
        # Run triage analysis
        triage_result = await self.gemini_client.triage_analysis(inv, evidence_summary)
        
        # Update investigation with results
        risk_score = triage_result.get('risk_score', 0.5)
        confidence = triage_result.get('confidence', 0.0)
        classification = triage_result.get('classification', 'SUSPICIOUS')
        
        # Map Gemini's classification to risk level
        risk_level = self._map_classification_to_risk_level(classification, risk_score)
        
        await self.state_manager.update_investigation(inv_id, {
            'risk_score': risk_score,
            'confidence': confidence,
            'risk_level': risk_level,
            'gemini_analysis': triage_result
        })
        
        # Generate detailed report if risk is high and confidence is good
        if risk_score >= 0.5 and confidence >= 0.6:
            logger.info(f"[{inv_id}] High risk detected ({risk_score:.2f}), generating detailed report...")
            await self._generate_detailed_report(inv_id, inv, evidence_summary, triage_result)
        
        logger.info(f"[{inv_id}] Analysis complete: risk={risk_score:.2f}, confidence={confidence:.2f}")
        
    async def _phase_deep_investigation(self, inv_id: str, inv: Dict):
        """Phase 3: Deep investigation (conditional)"""
        logger.info(f"[{inv_id}] Phase: DEEP_INVESTIGATION")
        
        await self.state_manager.update_investigation(inv_id, {
            'status': 'DEEP_INVESTIGATION',
            'current_phase': 'DEEP_INVESTIGATION'
        })
        
        # Get all evidence
        evidence_items = await self.state_manager.get_evidence(inv_id)
        evidence_summary = self.evidence_processor.summarize_evidence(evidence_items)
        
        # Run deep analysis
        deep_result = await self.gemini_client.deep_forensic_analysis(inv, evidence_summary)
        
        # Update with deep analysis
        risk_assessment = deep_result.get('risk_assessment', {})
        risk_score = risk_assessment.get('score', 0.5)
        confidence = risk_assessment.get('confidence', 0.0)
        classification = risk_assessment.get('classification', 'SUSPICIOUS')
        
        # Map Gemini's classification to risk level
        risk_level = self._map_classification_to_risk_level(classification, risk_score)
        
        await self.state_manager.update_investigation(inv_id, {
            'gemini_analysis': deep_result,
            'risk_score': risk_score,
            'confidence': confidence,
            'risk_level': risk_level
        })
        
        # Generate detailed report if not already generated and risk is high
        inv_updated = await self.state_manager.get_investigation(inv_id)
        if not inv_updated.get('detailed_report') and risk_score >= 0.5 and confidence >= 0.6:
            logger.info(f"[{inv_id}] Generating detailed report after deep investigation...")
            await self._generate_detailed_report(inv_id, inv, evidence_summary, deep_result)
        
        logger.info(f"[{inv_id}] Deep investigation complete")
        
    async def _phase_monitoring(self, inv_id: str, inv: Dict):
        """Phase 4: Continuous monitoring"""
        logger.info(f"[{inv_id}] Phase: MONITORING")
        
        await self.state_manager.update_investigation(inv_id, {
            'status': 'MONITORING',
            'current_phase': 'MONITORING'
        })
        
        # Monitor for a short period (in production, this would be longer)
        await asyncio.sleep(10)
        
        logger.info(f"[{inv_id}] Monitoring complete")
        
    async def _phase_completed(self, inv_id: str):
        """Phase 5: Complete investigation"""
        logger.info(f"[{inv_id}] Phase: COMPLETED")
        
        inv = await self.state_manager.get_investigation(inv_id)
        
        # Generate summary
        summary = self._generate_summary(inv)
        
        await self.state_manager.update_investigation(inv_id, {
            'status': 'COMPLETED',
            'current_phase': 'COMPLETED',
            'completed_at': datetime.utcnow().isoformat(),
            'summary': summary,
            'is_active': False
        })
        
        logger.info(f"✅ Investigation {inv_id} completed")
        
    def _map_classification_to_risk_level(self, classification: str, risk_score: float) -> str:
        """Map Gemini's classification to risk level, with score as fallback"""
        classification_map = {
            'BENIGN': 'LOW',
            'SUSPICIOUS': 'MEDIUM',
            'LIKELY_MALWARE': 'HIGH',
            'CONFIRMED_THREAT': 'CRITICAL'
        }
        
        # Use Gemini's classification if available
        if classification in classification_map:
            return classification_map[classification]
        
        # Fallback to score-based classification (0-1 scale mapped to your ranges)
        # Low: 0.01 – 0.39 (1% - 39%)
        # Medium: 0.40 – 0.69 (40% - 69%)
        # High: 0.70 – 0.89 (70% - 89%)
        # Critical: 0.90 – 1.00 (90% - 100%)
        if risk_score >= 0.90:
            return 'CRITICAL'
        elif risk_score >= 0.70:
            return 'HIGH'
        elif risk_score >= 0.40:
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _calculate_risk_level(self, risk_score: float) -> str:
        """Calculate risk level from score (deprecated - use _map_classification_to_risk_level)"""
        if risk_score >= 0.90:
            return 'CRITICAL'
        elif risk_score >= 0.70:
            return 'HIGH'
        elif risk_score >= 0.40:
            return 'MEDIUM'
        else:
            return 'LOW'
            
    def _generate_summary(self, inv: Dict) -> str:
        """Generate investigation summary"""
        risk_level = inv.get('risk_level', 'UNKNOWN')
        risk_score = inv.get('risk_score', 0)
        process_name = inv.get('process_name', 'Unknown')
        
        return f"Investigation of {process_name} (PID {inv['pid']}) completed. Risk: {risk_level} ({risk_score:.2f})"
    
    async def _generate_detailed_report(self, inv_id: str, inv: Dict, evidence_summary: Dict, analysis_result: Dict):
        """Generate detailed Markdown report written by Gemini"""
        try:
            logger.info(f"[{inv_id}] Generating detailed Markdown report...")
            
            # Get all queries for this investigation (not just count)
            queries = []
            try:
                async with self.state_manager.db.execute(
                    "SELECT * FROM gemini_queries WHERE investigation_id = ? ORDER BY created_at",
                    (inv_id,)
                ) as cursor:
                    query_rows = await cursor.fetchall()
                    queries = [dict(row) for row in query_rows]
            except Exception as e:
                logger.warning(f"[{inv_id}] Could not get queries: {e}")
            
            # Generate Markdown report using Gemini
            markdown_report = await self.gemini_client.generate_detailed_report(
                inv, evidence_summary, analysis_result, queries
            )
            
            # Store report in database
            await self.state_manager.update_investigation(inv_id, {
                'detailed_report_md': markdown_report,
                'report_generated_at': datetime.utcnow().isoformat()
            })
            
            logger.info(f"[{inv_id}] ✅ Detailed Markdown report generated and stored ({len(markdown_report)} chars)")
            
        except Exception as e:
            logger.error(f"[{inv_id}] ❌ Failed to generate detailed report: {e}", exc_info=True)
    
    async def _generate_interval_detailed_report(self, interval_id: int, interval: Dict, gemini_response: Dict):
        """Generate detailed Markdown report for interval analysis"""
        try:
            logger.info(f"📄 Generating detailed report for interval {interval_id}...")
            
            # Get queries for this interval
            interval_start = interval.get('interval_start')
            interval_end = interval.get('interval_end')
            
            queries = []
            try:
                async with self.state_manager.db.execute("""
                    SELECT * FROM gemini_queries
                    WHERE created_at >= ? AND created_at <= ?
                    ORDER BY created_at
                """, (interval_start, interval_end)) as cursor:
                    query_rows = await cursor.fetchall()
                    queries = [dict(row) for row in query_rows]
            except Exception as e:
                logger.warning(f"Could not fetch queries for interval {interval_id}: {e}")
            
            # Generate report using Gemini
            markdown_report = await self.gemini_client.generate_interval_detailed_report(
                interval, gemini_response, queries
            )
            
            # Store report in database
            await self.state_manager.db.execute("""
                UPDATE summary_intervals
                SET detailed_report_md = ?, report_generated_at = ?
                WHERE id = ?
            """, (markdown_report, datetime.utcnow().isoformat(), interval_id))
            await self.state_manager.db.commit()
            
            logger.info(f"✅ Detailed report generated and stored for interval {interval_id} ({len(markdown_report)} chars)")
            
        except Exception as e:
            logger.error(f"❌ Failed to generate interval report: {e}", exc_info=True)
        
    async def resume_incomplete_investigations(self):
        """Resume investigations after restart"""
        incomplete = await self.state_manager.get_incomplete_investigations()
        
        if incomplete:
            logger.info(f"Resuming {len(incomplete)} incomplete investigations")
            
            for inv in incomplete:
                inv_id = inv['id']
                logger.info(f"Resuming investigation: {inv_id}")
                
                # Resume from last phase
                task = asyncio.create_task(self._run_investigation(inv_id))
                self.active_investigations[inv_id] = task
                
    async def get_active_count(self) -> int:
        """Get count of active investigations"""
        return len(self.active_investigations)
        
    async def stop(self):
        """Stop orchestrator"""
        logger.info("Stopping orchestrator...")
        
        # Cancel all active investigations
        for inv_id, task in self.active_investigations.items():
            task.cancel()
            
        # Wait for cancellation
        if self.active_investigations:
            await asyncio.gather(*self.active_investigations.values(), return_exceptions=True)
            
        self.active_investigations.clear()
    
    async def analyze_latest_interval(self) -> Optional[Dict[str, Any]]:
        """Analyze latest interval summary with Gemini (autonomous querying)"""
        # Get latest unsent summary
        async with self.state_manager.db.execute("""
            SELECT * FROM summary_intervals
            WHERE sent_to_gemini = 0
            ORDER BY interval_start DESC
            LIMIT 1
        """) as cursor:
            summary = await cursor.fetchone()
            
        if not summary:
            return None
            
        logger.info(f"📊 Analyzing interval: {summary['interval_start']}")
        
        # Analyze with Gemini (may trigger autonomous queries)
        result = await self.gemini_client.analyze_interval_summary(dict(summary))
        
        # Mark as sent and store response
        await self.state_manager.db.execute("""
            UPDATE summary_intervals
            SET sent_to_gemini = 1, gemini_response = ?
            WHERE id = ?
        """, (json.dumps(result), summary['id']))
        await self.state_manager.db.commit()
        
        # Check if we should generate a detailed report (risk >= 50% and confidence >= 60%)
        risk_score = result.get('risk_score', 0)
        confidence = result.get('confidence', 0)
        
        if risk_score >= 0.5 and confidence >= 0.6:
            logger.info(f"📄 High risk interval detected ({risk_score:.2f} risk, {confidence:.2f} confidence) - generating detailed report...")
            await self._generate_interval_detailed_report(summary['id'], dict(summary), result)
        
        # If threats identified, trigger investigations
        threats = result.get('threats_identified', [])
        for threat in threats:
            if threat.get('recommended_action') == 'INVESTIGATE':
                logger.info(f"🚨 Threat identified: PID {threat['pid']} - {threat['threat_type']}")
                # Trigger investigation for this process
                await self.trigger_investigation({
                    'pid': threat['pid'],
                    'process_name': threat['process_name'],
                    'trigger_reasons': [f"Gemini autonomous detection: {threat['threat_type']}"],
                    'triggered_at': datetime.utcnow().isoformat()
                })
                
        return result
