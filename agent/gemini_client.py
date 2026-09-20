"""
Gemini AI Client
Interfaces with Gemini 2.5 Flash for forensic reasoning

Gemini 2.5 Flash Features:
- Dynamic thinking mode enabled by default
- thinking_level="low" for fast triage (speed optimized)
- thinking_level="high" for deep analysis (reasoning optimized)
- Temperature kept at 1.0 (recommended for thinking models)
- Up to 1M token context window
- Autonomous querying capability for raw process data
"""

from google import genai
from google.genai import types
from typing import Dict, Any, Optional, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class GeminiClient:
    """Client for Gemini 2.5 Flash reasoning with autonomous querying"""
    
    def __init__(self, config, query_handler=None):
        self.config = config
        self.query_handler = query_handler
        
        # Initialize Gemini client
        self.client = genai.Client(api_key=config.gemini_api_key) if config.live_ai_enabled else None
        self.model_name = config.gemini_model_pro
        
        logger.info(f"✅ Gemini 2.5 Flash initialized: {self.model_name}")
        if query_handler:
            logger.info("✅ Autonomous querying enabled")
        
    async def triage_analysis(self, process_data: Dict[str, Any], 
                              evidence_summary: str) -> Dict[str, Any]:
        """
        Fast triage using Gemini 2.5 Flash with low thinking level
        
        Uses thinking_level="low" for rapid initial assessment:
        - Faster response time
        - Lower cost
        - Sufficient for initial risk scoring
        
        Returns: risk_score, confidence, should_investigate_deeper
        """
        logger.info(f"🧠 Running Gemini 2.5 Flash triage for PID {process_data['pid']} (thinking_level: low)")
        
        prompt = self._build_triage_prompt(process_data, evidence_summary)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_level="low")
                )
            )
            
            # Clean response text (remove markdown code blocks if present)
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Handle case where Gemini returns an array instead of object
            if isinstance(result, list):
                logger.warning(f"⚠️ Gemini returned array instead of object, using first item")
                result = result[0] if result else {}
            
            # Validate that confidence was provided by AI
            if 'confidence' not in result or result['confidence'] is None:
                logger.error(f"❌ Gemini did NOT provide confidence value in triage response!")
                logger.error(f"   This should not happen - AI must decide confidence")
                result['confidence'] = 0.0  # Fallback to indicate missing data
            
            logger.info(f"✅ Triage complete: risk={result.get('risk_score', 0):.2f}, confidence={result.get('confidence', 0):.2f}")
            logger.info(f"   Classification: {result.get('classification', 'UNKNOWN')}")
            logger.info(f"   Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini triage error: {e}")
            logger.error(f"   Response text: {response.text if 'response' in locals() else 'No response'}")
            return {
                'risk_score': 0.5,
                'confidence': 0.0,
                'should_investigate_deeper': True,
                'error': str(e)
            }
    
    async def analyze_interval_summary(self, summary: Dict[str, Any], 
                                      investigation_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze 1-minute interval summary with autonomous querying
        
        Gemini can request additional details by returning queries in response.
        This enables autonomous investigation of suspicious patterns.
        """
        logger.info(f"🧠 Analyzing interval summary with autonomous querying")
        
        prompt = self._build_interval_analysis_prompt(summary)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_level="low")
                )
            )
            
            # Clean response
            response_text = response.text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Handle case where Gemini returns an array instead of object
            if isinstance(result, list):
                logger.warning(f"⚠️ Gemini returned array instead of object, using first item")
                result = result[0] if result else {}
            
            # Validate that confidence was provided by AI
            if 'confidence' not in result or result['confidence'] is None:
                # Check if we can derive it from threats
                threats = result.get('threats_identified', [])
                if threats and all('confidence' in t for t in threats):
                    # Calculate average confidence from threats
                    avg_confidence = sum(t['confidence'] for t in threats) / len(threats)
                    logger.warning(f"⚠️ Gemini did NOT provide top-level confidence, calculated from threats: {avg_confidence:.2f}")
                    result['confidence'] = avg_confidence
                else:
                    logger.error(f"❌ Gemini did NOT provide confidence value in interval analysis!")
                    logger.error(f"   This should not happen - AI must decide confidence")
                    result['confidence'] = 0.0  # Fallback to indicate missing data
            
            # Check if Gemini wants to query for more details
            if result.get('needs_more_data') and self.query_handler:
                queries = result.get('queries', [])
                logger.info(f"🔍 Gemini requesting {len(queries)} autonomous queries")
                
                # Execute queries
                query_results = []
                for query in queries:
                    query_result = await self.query_handler.handle_query(query, investigation_id)
                    query_results.append(query_result)
                    
                # Re-analyze with query results
                result = await self._reanalyze_with_query_results(
                    summary, query_results, investigation_id
                )
                
            logger.info(f"✅ Interval analysis: risk={result.get('risk_score', 0):.2f}, suspicious={result.get('suspicious_count', 0)}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Interval analysis error: {e}")
            return {
                'risk_score': 0.0,
                'suspicious_count': 0,
                'error': str(e)
            }
    
    async def _reanalyze_with_query_results(self, summary: Dict, 
                                           query_results: list,
                                           investigation_id: Optional[str]) -> Dict[str, Any]:
        """Re-analyze with additional query results"""
        logger.info(f"🔬 Re-analyzing with {len(query_results)} query results")
        
        prompt = f"""You previously analyzed this interval summary and requested additional data.

**Original Summary:**
{json.dumps(summary, indent=2)}

**Query Results:**
{json.dumps(query_results, indent=2)}

**Task:**
Now provide your final analysis with the additional context. Return ONLY valid JSON:
{{
  "risk_score": 0.0-1.0,
  "confidence": 0.0-1.0,
  "suspicious_count": 0,
  "threats_identified": [
    {{
      "pid": 1234,
      "process_name": "example.exe",
      "threat_type": "MALWARE|SUSPICIOUS|ANOMALY",
      "confidence": 0.0-1.0,
      "evidence": ["list of evidence"],
      "recommended_action": "INVESTIGATE|MONITOR|IGNORE"
    }}
  ],
  "summary": "brief analysis"
}}

**CRITICAL: You MUST provide a top-level confidence field (0.0-1.0) indicating your overall confidence in this analysis.**"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(thinking_level="high")
                )
            )
            
            response_text = response.text.strip()
            if response_text.startswith('```'):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Validate that confidence was provided by AI
            if 'confidence' not in result or result['confidence'] is None:
                # Check if we can derive it from threats
                threats = result.get('threats_identified', [])
                if threats and all('confidence' in t for t in threats):
                    # Calculate average confidence from threats
                    avg_confidence = sum(t['confidence'] for t in threats) / len(threats)
                    logger.warning(f"⚠️ Gemini did NOT provide top-level confidence in re-analysis, calculated from threats: {avg_confidence:.2f}")
                    result['confidence'] = avg_confidence
                else:
                    logger.error(f"❌ Gemini did NOT provide confidence value in re-analysis!")
                    result['confidence'] = 0.0
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Re-analysis error: {e}")
            return {
                'risk_score': 0.5,
                'suspicious_count': 0,
                'error': str(e)
            }
        
    async def deep_forensic_analysis(self, process_data: Dict[str, Any],
                                     all_evidence: str) -> Dict[str, Any]:
        """
        Deep forensic analysis using Gemini 2.5 Flash with high thinking level
        
        Uses thinking_level="high" for comprehensive investigation:
        - Dynamic reasoning depth (model decides based on complexity)
        - include_thoughts=True to expose reasoning process
        - Maximum context utilization (up to 1M tokens)
        - Explicit uncertainty tracking
        
        Returns: comprehensive forensic report with MITRE ATT&CK mapping
        """
        logger.info(f"🔬 Running Gemini 2.5 Flash DEEP analysis for PID {process_data['pid']} (thinking_level: high)")
        
        prompt = self._build_forensic_prompt(process_data, all_evidence)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    response_mime_type="application/json",
                    thinking_config=types.ThinkingConfig(
                        thinking_level="high",
                        include_thoughts=True  # Show reasoning process
                    )
                )
            )
            
            # Clean response text (remove markdown code blocks if present)
            response_text = response.text.strip()
            if response_text.startswith('```'):
                # Remove markdown code blocks
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace('```json', '').replace('```', '').strip()
            
            result = json.loads(response_text)
            
            # Handle case where Gemini returns an array instead of object
            if isinstance(result, list):
                logger.warning(f"⚠️ Gemini returned array instead of object, using first item")
                result = result[0] if result else {}
            
            # Validate that confidence was provided by AI in risk_assessment
            risk_assessment = result.get('risk_assessment', {})
            if 'confidence' not in risk_assessment or risk_assessment['confidence'] is None:
                logger.error(f"❌ Gemini did NOT provide confidence value in deep analysis!")
                logger.error(f"   This should not happen - AI must decide confidence")
                risk_assessment['confidence'] = 0.0  # Fallback to indicate missing data
                result['risk_assessment'] = risk_assessment
            
            # Log detailed analysis
            logger.info(f"✅ Deep analysis complete:")
            logger.info(f"   Risk: {risk_assessment.get('score', 0):.2f} ({risk_assessment.get('classification', 'UNKNOWN')})")
            logger.info(f"   Confidence: {risk_assessment.get('confidence', 0):.2f}")
            logger.info(f"   MITRE Techniques: {', '.join(risk_assessment.get('mitre_techniques', []))}")
            
            # Log uncertainties
            uncertainties = result.get('uncertainties', [])
            if uncertainties:
                logger.info(f"   Uncertainties: {len(uncertainties)} items")
                for unc in uncertainties[:2]:
                    logger.info(f"     - {unc}")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Gemini deep analysis error: {e}")
            logger.error(f"   Response text: {response.text if 'response' in locals() else 'No response'}")
            return {
                'risk_assessment': {
                    'score': 0.5,
                    'confidence': 0.0,
                    'classification': 'UNKNOWN'
                },
                'error': str(e)
            }
            
    def _build_triage_prompt(self, process_data: Dict, evidence: str) -> str:
        """Build prompt for triage analysis"""
        return f"""You are a cybersecurity forensic analyst performing rapid triage on a suspicious process.

**Process Information:**
- PID: {process_data['pid']}
- Name: {process_data['process_name']}
- Path: {process_data.get('process_path', 'Unknown')}
- Parent: {process_data.get('parent_name', 'Unknown')} (PID {process_data.get('parent_pid', 'Unknown')})
- Command Line: {process_data.get('command_line', 'Unknown')}
- User: {process_data.get('user_name', 'Unknown')}
- Trigger Reasons: {', '.join(process_data.get('trigger_reasons', []))}

**Initial Evidence:**
{evidence}

**Task:**
Perform rapid risk assessment. Return ONLY valid JSON (no markdown, no code blocks) with:
{{
  "risk_score": 0.0-1.0,
  "confidence": 0.0-1.0,  // REQUIRED: Your confidence in this assessment
  "classification": "BENIGN|SUSPICIOUS|LIKELY_MALWARE|CONFIRMED_THREAT",
  "should_investigate_deeper": true/false,
  "key_indicators": ["list", "of", "indicators"],
  "reasoning": "brief explanation"
}}

**CRITICAL: You MUST provide a confidence value (0.0-1.0) based on:**
- 0.9-1.0: Very confident (clear, unambiguous indicators)
- 0.7-0.9: Confident (strong evidence, minor uncertainties)
- 0.5-0.7: Moderate confidence (some conflicting signals)
- 0.3-0.5: Low confidence (limited data, unclear patterns)
- 0.0-0.3: Very uncertain (need more investigation)

Be conservative. When uncertain, recommend deeper investigation."""
        
    def _build_forensic_prompt(self, process_data: Dict, evidence: str) -> str:
        """Build prompt for deep forensic analysis"""
        return f"""You are an expert cybersecurity forensic analyst conducting a comprehensive investigation.

**Process Under Investigation:**
- PID: {process_data['pid']}
- Name: {process_data['process_name']}
- Path: {process_data.get('process_path', 'Unknown')}
- Parent: {process_data.get('parent_name', 'Unknown')}
- Command Line: {process_data.get('command_line', 'Unknown')}
- User: {process_data.get('user_name', 'Unknown')}

**Complete Evidence Package:**
{evidence}

**Task:**
Conduct comprehensive forensic analysis. Return ONLY valid JSON (no markdown, no code blocks) with:
{{
  "risk_assessment": {{
    "score": 0.0-1.0,
    "confidence": 0.0-1.0,  // REQUIRED: Your confidence in this assessment
    "classification": "BENIGN|SUSPICIOUS|LIKELY_MALWARE|CONFIRMED_THREAT",
    "mitre_techniques": ["T1059", "T1083"]
  }},
  "attack_chain": {{
    "initial_access": "description",
    "execution": "description",
    "persistence": "description",
    "observed_indicators": ["list"]
  }},
  "evidence_quality": "LOW|MEDIUM|HIGH",
  "uncertainties": ["what we don't know"],
  "recommended_next_steps": ["actions"],
  "false_positive_check": "likelihood and reasoning"
}}

**Critical Instructions:**
1. **CONFIDENCE IS REQUIRED**: You MUST provide confidence (0.0-1.0) in risk_assessment
   - 0.9-1.0: Very confident (clear, unambiguous evidence)
   - 0.7-0.9: Confident (strong evidence, minor gaps)
   - 0.5-0.7: Moderate (some conflicting signals)
   - 0.3-0.5: Low (limited data, unclear patterns)
   - 0.0-0.3: Very uncertain (need more data)
2. Explicitly state what you DON'T know
3. Separate facts from assumptions
4. Consider false positive scenarios
5. Be precise about confidence levels"""
    
    def _build_interval_analysis_prompt(self, summary: Dict) -> str:
        """Build prompt for interval summary analysis"""
        query_protocol = ""
        if self.query_handler:
            query_protocol = self.query_handler.get_query_protocol_description()
            
        return f"""You are analyzing a 1-minute system activity summary for security threats.

**Interval Summary:**
- Time: {summary.get('interval_start')} to {summary.get('interval_end')}
- Total Processes: {summary.get('total_processes', 0)}
- New Processes: {summary.get('new_processes', 0)}
- Suspicious Patterns: {len(json.loads(summary.get('suspicious_patterns', '[]')))}
- High CPU: {len(json.loads(summary.get('high_cpu_processes', '[]')))}
- Network Activity: {len(json.loads(summary.get('high_network_processes', '[]')))}

**Suspicious Patterns:**
{json.dumps(json.loads(summary.get('suspicious_patterns', '[]')), indent=2)}

**High CPU Processes:**
{json.dumps(json.loads(summary.get('high_cpu_processes', '[]')), indent=2)}

**Network Activity:**
{json.dumps(json.loads(summary.get('high_network_processes', '[]')), indent=2)}

{query_protocol}

**Task:**
Analyze this summary. If you need more details about specific processes or patterns, 
you can request queries. Return ONLY valid JSON:

{{
  "risk_score": 0.0-1.0,
  "confidence": 0.0-1.0,  // REQUIRED: Your confidence in this assessment
  "suspicious_count": 0,
  "needs_more_data": true/false,
  "queries": [
    {{
      "action": "QUERY_PROCESS",
      "process_id": 1234,
      "time_range": "last_5_minutes",
      "details": ["network", "file_access"]
    }}
  ],
  "initial_assessment": "brief analysis",
  "concerns": ["list of concerns"]
}}

**Confidence Guidelines:**
- 0.9-1.0: Very confident in assessment (clear indicators)
- 0.7-0.9: Confident (strong evidence)
- 0.5-0.7: Moderate confidence (some uncertainty)
- 0.3-0.5: Low confidence (limited data)
- 0.0-0.3: Very uncertain (need more investigation)

**CRITICAL: You MUST provide a confidence value. This tells analysts how certain you are.**

If nothing suspicious, set needs_more_data=false and queries=[]."""

    async def generate_detailed_report(self, investigation: Dict, evidence_summary: Dict, analysis_result: Dict, queries: List[Dict] = None) -> str:
        """Generate a detailed Markdown report written by Gemini in its own words"""
        logger.info(f"📄 Generating detailed Markdown report for {investigation.get('id', 'autonomous investigation')}")
        
        # Process queries to extract useful information
        if queries is None:
            queries = []
        
        query_summary = []
        for q in queries:
            query_summary.append({
                'query_type': q.get('query_type'),
                'params': json.loads(q.get('query_params', '{}')),
                'result_count': q.get('result_count', 0),
                'findings': json.loads(q.get('result_data', '{}'))
            })
        
        # Build context for Gemini
        context = f"""**INVESTIGATION CONTEXT:**
- Process: {investigation.get('process_name', 'Multiple processes')}
- PID: {investigation.get('pid', 'N/A')}
- Parent: {investigation.get('parent_name', 'Unknown')} (PID {investigation.get('parent_pid', 'N/A')})
- Command: {investigation.get('command_line', 'N/A')}
- User: {investigation.get('user_name', 'N/A')}
- Path: {investigation.get('process_path', 'N/A')}
- Triggered: {investigation.get('triggered_at', 'N/A')}
- Autonomous Queries Executed: {len(queries)}

**MY ANALYSIS RESULTS:**
{json.dumps(analysis_result, indent=2)}

**EVIDENCE I COLLECTED:**
{json.dumps(evidence_summary, indent=2)}

**AUTONOMOUS QUERIES I EXECUTED:**
{json.dumps(query_summary, indent=2) if query_summary else "No autonomous queries were executed during this investigation."}"""

        prompt = f"""You are Gemini 2.5 Flash, an AI security analyst. You just completed an autonomous investigation and now need to write a comprehensive report explaining what you found.

{context}

**YOUR TASK:**
Write a detailed investigation report in Markdown format. This is YOUR report - write it in first person, explaining what YOU did, what YOU found, and what YOU think.

**WRITING STYLE:**
- Write naturally, as if explaining to a colleague
- Use first person ("I analyzed...", "I discovered...")
- Be specific about your reasoning and confidence
- Explain technical details clearly
- Use Markdown formatting for structure

**MARKDOWN FORMATTING RULES:**
Use these special markers that will be highlighted with colors:

1. **Commands**: Wrap in backticks with `cmd:` prefix
   Example: `cmd:powershell.exe -enc JABhAD0...`

2. **File Paths**: Wrap in backticks with `path:` prefix
   Example: `path:C:\\Windows\\System32\\cmd.exe`

3. **IP Addresses**: Wrap in backticks with `ip:` prefix
   Example: `ip:192.168.1.100`

4. **Process Names**: Wrap in backticks with `proc:` prefix
   Example: `proc:powershell.exe`

5. **Critical Findings**: Use `> **🔴 CRITICAL:**` for blockquotes
   Example: > **🔴 CRITICAL:** This process attempted credential theft

6. **Warnings**: Use `> **🟠 WARNING:**` for blockquotes
   Example: > **🟠 WARNING:** Suspicious network connection detected

7. **Info**: Use `> **🔵 INFO:**` for blockquotes
   Example: > **🔵 INFO:** Process spawned by legitimate parent

8. **Code blocks**: Use triple backticks for multi-line code/commands

**REPORT STRUCTURE:**

# Investigation Report

## Executive Summary
[2-3 sentences for management - what happened and how serious it is]

## My Investigation Process

### What I Did
[Explain your investigation steps in first person]
- How you analyzed the initial data
- What patterns you investigated

### What I Found
[Your key findings from both initial evidence and query results]
- Findings from initial evidence collection
- Additional insights from autonomous queries
- Patterns that emerged from deeper investigation

## Risk Assessment

### My Verdict
- **Risk Score:** [X]%
- **Confidence:** [X]%
- **Classification:** [BENIGN/SUSPICIOUS/LIKELY_MALWARE/CONFIRMED_THREAT]

### Why This Score?
[Explain your reasoning - why did you assign this risk score? What made you confident or uncertain?]

### Confidence Factors
[What increased or decreased your confidence?]
- Factor 1
- Factor 2

## Timeline of Events
[Chronological breakdown of what happened]

## Technical Analysis

### Process Behavior
[What the process did - use the special markers for commands, paths, IPs, processes]

**IMPORTANT**: Based on the evidence provided, describe:
- **Execution Location**: Where the process was executed from (working directory, full path)
- **User Context**: Which user account executed it
- **Parent Process**: What spawned this process and why that matters
- **Child Processes**: Any processes it spawned
- **Command Line**: The full command line with arguments (if suspicious, explain what each part does)

### Network Activity
[If any - use `ip:` markers]

**IMPORTANT**: If network connections were detected in the evidence, describe:
- Remote IP addresses and ports
- Connection types (outbound/listening)
- Suspicious destinations
- If NO network activity: explicitly state "No network connections detected in evidence"

### File Operations
[If any - use `path:` markers]

**IMPORTANT**: Based on filesystem evidence, describe:
- Files accessed or modified
- Directories accessed
- Suspicious file paths
- If NO file operations: explicitly state "No file operations detected in evidence"

### Registry & Persistence
[If any registry or scheduled task evidence exists]

**IMPORTANT**: If registry or scheduled task evidence exists, describe:
- Registry keys modified
- Scheduled tasks created
- Persistence mechanisms
- If NO registry/persistence activity: explicitly state "No registry modifications or persistence mechanisms detected in evidence"

### Suspicious Patterns
[What caught your attention]

## Attack Chain (if malicious)
[Step-by-step breakdown of the attack]

1. **Initial Access**: [How it started]
2. **Execution**: [What it did]
3. **Persistence**: [If it tried to persist]
4. **Command & Control**: [If it connected out]

## Indicators of Compromise

### Critical
- [Most important IOCs]

### Warning
- [Suspicious indicators]

### Informational
- [Context indicators]

## My Recommendations

### Immediate Actions
1. [What to do right now]
2. [Priority actions]

### Follow-up Actions
1. [What to investigate further]
2. [Long-term recommendations]

## Technical Details

### MITRE ATT&CK Mapping
[If applicable]

### Additional Context
[Any other relevant technical information]

---

*Report generated by Gemini 2.5 Flash on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*

**IMPORTANT:**
- Write this as YOUR report - use "I" and "my"
- Be honest about uncertainties
- Use the special markers ```X``` (`cmd:`, `path:`, `ip:`, `proc:`) for highlighting
- Use blockquotes for critical/warning/info callouts
- Make it readable and professional
- Explain your reasoning clearly
- Make Sure to mention maybe the directory, maybe the connections, and is the process created any sheduled tasks or change registries etc info as well.

Return ONLY the Markdown text, no JSON wrapper."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    thinking_config=types.ThinkingConfig(thinking_level="high")
                )
            )
            
            # Get the markdown report
            markdown_report = response.text.strip()
            
            # Remove any markdown code block wrappers if Gemini added them
            if markdown_report.startswith('```markdown'):
                markdown_report = markdown_report[11:]
            if markdown_report.startswith('```'):
                markdown_report = markdown_report[3:]
            if markdown_report.endswith('```'):
                markdown_report = markdown_report[:-3]
            
            markdown_report = markdown_report.strip()
            
            logger.info(f"✅ Detailed Markdown report generated ({len(markdown_report)} characters)")
            
            return markdown_report
            
        except Exception as e:
            logger.error(f"❌ Report generation error: {e}")
            return f"""# Investigation Report

## Error

I encountered an error while generating this report: {str(e)}

Please check the logs for more details.

---

*Report generation failed on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*
"""


    async def generate_interval_detailed_report(self, interval: Dict, gemini_response: Dict, queries: List[Dict]) -> str:
        """Generate a detailed Markdown report for interval analysis written by Gemini"""
        logger.info(f"📄 Generating detailed interval report for {interval.get('interval_start')}")
        
        # Parse data from interval
        suspicious_patterns = json.loads(interval.get('suspicious_patterns', '[]'))
        high_cpu = json.loads(interval.get('high_cpu_processes', '[]'))
        high_network = json.loads(interval.get('high_network_processes', '[]'))
        
        # Build context for Gemini
        context = f"""**INTERVAL ANALYSIS CONTEXT:**
- Time Range: {interval.get('interval_start')} to {interval.get('interval_end')}
- Total Processes: {interval.get('total_processes', 0)}
- Suspicious Patterns: {len(suspicious_patterns)}
- High CPU Processes: {len(high_cpu)}
- High Network Processes: {len(high_network)}
- Autonomous Queries Executed: {len(queries)}

**SUSPICIOUS PATTERNS DETECTED:**
{json.dumps(suspicious_patterns, indent=2)}

**HIGH CPU PROCESSES:**
{json.dumps(high_cpu, indent=2)}

**HIGH NETWORK PROCESSES:**
{json.dumps(high_network, indent=2)}

**MY ANALYSIS RESULTS:**
{json.dumps(gemini_response, indent=2)}

**AUTONOMOUS QUERIES I EXECUTED:**
{json.dumps(queries, indent=2)}

**QUERY RESULTS (what I learned):**
{json.dumps([{'query_type': q.get('query_type'), 'params': q.get('query_params'), 'result_count': q.get('result_count'), 'findings': q.get('result_data')} for q in queries], indent=2)}"""

        prompt = f"""You are Gemini 2.5 Flash, an AI security analyst. You just completed an autonomous investigation of a 1-minute monitoring interval and now need to write a comprehensive report explaining what you found.

{context}

**YOUR TASK:**
Write a detailed investigation report in Markdown format. This is YOUR report - write it in first person, explaining what YOU did, what YOU found, and what YOU think.

**CRITICAL INSTRUCTIONS:**
1. **Use the actual data provided** - The query results above show what you learned. Use them!
2. **Be specific about processes** - Mention process names, PIDs, parent processes, execution paths from the query results
3. **Explain behaviors** - What did each suspicious process actually do? Use the data!
4. **State what's missing** - If no network activity in the data, say "No network connections detected"

**WRITING STYLE:**
- Write naturally, as if explaining to a colleague
- Use first person ("I analyzed...", "I discovered...")
- Be specific - use actual process names, paths, PIDs from the data
- Explain your reasoning clearly

**MARKDOWN FORMATTING:**
- `cmd:command` for commands
- `path:C:\\path` for file paths
- `ip:192.168.1.1` for IP addresses
- `proc:process.exe` for process names
- `> **🔴 CRITICAL:**` for critical findings
- `> **🟠 WARNING:**` for warnings
- `> **🔵 INFO:**` for informational notes

**REPORT STRUCTURE:**

# Autonomous Investigation Report

## Executive Summary
[2-3 sentences - what happened and how serious]

## My Investigation Process

### What I Did
- Monitored [X] processes during this interval
- Detected [X] suspicious patterns
- Used thinking_level="[low/high]" for [fast/deep] analysis

### What I Found
[Key findings - be specific with process names, PIDs, behaviors from the data]

## Risk Assessment

### My Verdict
- **Risk Score:** [X]%
- **Confidence:** [X]%
- **Classification:** [BENIGN/SUSPICIOUS/THREAT]

### Why This Score?
[Your reasoning based on the actual data]

## Detailed Analysis

### Suspicious Processes

For each suspicious process in the data, create a section:

#### `proc:[ProcessName]` (PID [X])

**Execution Context:**
- **Parent Process:** [from query results if available]
- **Execution Path:** `path:[full path from data]`
- **Command Line:** `cmd:[full command from data]`
- **Working Directory:** `path:[directory from data]`
- **User:** [user account from data]

**Behavior Observed:**
- [What it did - from the data]
- Network: [connections from data or "None detected"]
- Files: [file access from data or "None detected"]
- Children: [spawned processes from data or "None spawned"]

**My Assessment:**
[Why this is suspicious/benign based on the evidence]

## Network Activity
[Describe actual network connections from the data, or state "No network connections detected during this interval"]

## File Operations
[Describe actual file operations from the data, or state "No file operations detected during this interval"]

## Registry & Persistence
[Describe any registry/scheduled task activity from the data, or state "No registry modifications or persistence mechanisms detected"]

## My Recommendations

### Immediate Actions
1. [Specific actions based on findings]

### Follow-up Actions
1. [What to investigate further]

---

*Report generated by Gemini 2.5 Flash on {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}*

**REMEMBER:** Use the actual data provided! Don't make up information. If something isn't in the data, explicitly state it wasn't detected."""

        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=1.0,
                    thinking_config=types.ThinkingConfig(thinking_level="high")
                )
            )
            
            markdown_report = response.text.strip()
            
            # Clean up any code fences
            if markdown_report.startswith('```markdown'):
                markdown_report = markdown_report.replace('```markdown\n', '').replace('\n```', '')
            elif markdown_report.startswith('```'):
                markdown_report = markdown_report.replace('```\n', '').replace('\n```', '')
            
            logger.info(f"✅ Interval detailed report generated ({len(markdown_report)} chars)")
            
            return markdown_report
            
        except Exception as e:
            logger.error(f"❌ Failed to generate interval report: {e}", exc_info=True)
            return f"# Error Generating Report\n\nFailed to generate detailed report: {str(e)}"
