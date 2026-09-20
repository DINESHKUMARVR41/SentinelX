import { useState, useEffect } from 'react';
import { X } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

const DetailedReportModal = ({ investigationId, summaryData, geminiResponse, onClose }) => {
  const [reportMarkdown, setReportMarkdown] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReport();
  }, [investigationId]);

  const fetchReport = async () => {
    try {
      setLoading(true);
      
      // Try to fetch from investigations table first
      let response = await fetch(`http://localhost:8000/investigations/${investigationId}/detailed-report`);
      
      if (!response.ok) {
        // If not found in investigations, generate from summary data
        if (summaryData && geminiResponse) {
          const generatedReport = await generateReportFromGemini(summaryData, geminiResponse);
          setReportMarkdown(generatedReport);
          setLoading(false);
          return;
        }
        throw new Error('Report not available');
      }
      
      const data = await response.json();
      setReportMarkdown(data.report_markdown);
      setLoading(false);
    } catch (err) {
      setError(err.message);
      setLoading(false);
    }
  };

  const generateReportFromGemini = async (summary, gemini) => {
    try {
      // Call the new Gemini-powered report generation endpoint
      const response = await fetch(`http://localhost:8000/api/investigations/intervals/${summary.id}/generate-report`, {
        method: 'POST'
      });
      
      if (!response.ok) {
        throw new Error(`API returned ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (!data.report) {
        throw new Error('No report content in API response');
      }
      
      return data.report;
      
    } catch (error) {
      console.error('Failed to generate Gemini report:', error);
      
      // Fallback to basic template if API fails
      const suspiciousPatterns = JSON.parse(summary.suspicious_patterns || '[]');
      const riskScore = gemini.risk_score || 0;
      const confidence = gemini.confidence || 0;
      
      return `# Autonomous Investigation Report

## Executive Summary

⚠️ **Note:** This is a fallback report. Gemini-powered report generation failed: ${error.message}

**Risk Level:** ${gemini.classification || 'UNKNOWN'}  
**Risk Score:** ${(riskScore * 100).toFixed(0)}%  
**Confidence:** ${(confidence * 100).toFixed(0)}%  
**Analysis Time:** ${new Date(summary.interval_start).toLocaleTimeString()} - ${new Date(summary.interval_end).toLocaleTimeString()}

## Basic Information

- **Total Processes:** ${summary.total_processes || 0}
- **Suspicious Patterns:** ${suspiciousPatterns.length}
- **Summary:** ${summary.summary_text || 'No summary available'}

${suspiciousPatterns.length > 0 ? `
## Suspicious Patterns Detected

${suspiciousPatterns.map(p => `- **${p.pattern}**: PID ${p.pid} (${p.name || 'Unknown'})`).join('\n')}
` : ''}

---

*Fallback report - Gemini analysis unavailable*
`;
    }
  };

  // Custom component to handle special markers
  const processInlineCode = (text) => {
    // Check for special prefixes
    if (text.startsWith('cmd:')) {
      return <code className="marker-cmd">{text.substring(4)}</code>;
    }
    if (text.startsWith('path:')) {
      return <code className="marker-path">{text.substring(5)}</code>;
    }
    if (text.startsWith('ip:')) {
      return <code className="marker-ip">{text.substring(3)}</code>;
    }
    if (text.startsWith('proc:')) {
      return <code className="marker-process">{text.substring(5)}</code>;
    }
    // Default code styling
    return <code className="markdown-code">{text}</code>;
  };

  // Custom renderers for Markdown elements
  const components = {
    // Inline code with special markers
    code: ({ node, inline, className, children, ...props }) => {
      const text = String(children).replace(/\n$/, '');
      
      if (inline) {
        return processInlineCode(text);
      }
      
      // Code blocks
      return (
        <pre className="markdown-code-block">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
      );
    },
    
    // Blockquotes with emoji markers
    blockquote: ({ node, children, ...props }) => {
      // Safely extract text from node
      let text = '';
      try {
        if (node && node.children && node.children[0]) {
          if (node.children[0].children && node.children[0].children[0]) {
            text = node.children[0].children[0].value || '';
          }
        }
      } catch (e) {
        // Ignore errors, use default styling
      }
      
      if (text.includes('🔴 CRITICAL:')) {
        return <blockquote className="markdown-blockquote critical" {...props}>{children}</blockquote>;
      }
      if (text.includes('🟠 WARNING:')) {
        return <blockquote className="markdown-blockquote warning" {...props}>{children}</blockquote>;
      }
      if (text.includes('🔵 INFO:')) {
        return <blockquote className="markdown-blockquote info" {...props}>{children}</blockquote>;
      }
      
      return <blockquote className="markdown-blockquote" {...props}>{children}</blockquote>;
    },
    
    // Headings
    h1: ({ node, children, ...props }) => (
      <h1 className="markdown-h1" {...props}>{children}</h1>
    ),
    h2: ({ node, children, ...props }) => (
      <h2 className="markdown-h2" {...props}>{children}</h2>
    ),
    h3: ({ node, children, ...props }) => (
      <h3 className="markdown-h3" {...props}>{children}</h3>
    ),
    
    // Lists
    ul: ({ node, children, ...props }) => (
      <ul className="markdown-ul" {...props}>{children}</ul>
    ),
    ol: ({ node, children, ...props }) => (
      <ol className="markdown-ol" {...props}>{children}</ol>
    ),
    li: ({ node, children, ...props}) => (
      <li className="markdown-li" {...props}>{children}</li>
    ),
    
    // Paragraphs
    p: ({ node, children, ...props }) => (
      <p className="markdown-p" {...props}>{children}</p>
    ),
    
    // Strong/Bold
    strong: ({ node, children, ...props }) => (
      <strong className="markdown-strong" {...props}>{children}</strong>
    ),
    
    // Tables
    table: ({ node, children, ...props }) => (
      <div className="markdown-table-wrapper">
        <table className="markdown-table" {...props}>{children}</table>
      </div>
    ),
    
    // Horizontal rule
    hr: ({ node, ...props }) => (
      <hr className="markdown-hr" {...props} />
    ),
  };

  if (loading) {
    return (
      <div className="modal-overlay">
        <div className="modal-content detailed-report-modal">
          <div className="loading">
            <div className="loading-spinner"></div>
            <p>Gemini is preparing your detailed report...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="modal-overlay">
        <div className="modal-content detailed-report-modal">
          <button className="modal-close" onClick={onClose}>
            <X size={24} />
          </button>
          <div className="error-message">
            <h3>Report Not Available</h3>
            <p>{error}</p>
            <p className="hint">Detailed reports are generated for investigations with risk score ≥ 50% and confidence ≥ 60%</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content detailed-report-modal markdown-report" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose}>
          <X size={24} />
        </button>
        
        <div className="report-content">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={components}
          >
            {reportMarkdown}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
};

export default DetailedReportModal;
