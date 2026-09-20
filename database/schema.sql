-- PROCSee Database Schema
-- SQLite database for investigation state persistence

-- Main investigations table
CREATE TABLE IF NOT EXISTS investigations (
    id TEXT PRIMARY KEY,                    -- UUID (inv_abc123)
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    process_path TEXT,
    process_hash TEXT,                      -- SHA256 of executable
    parent_pid INTEGER,
    parent_name TEXT,
    command_line TEXT,
    user_name TEXT,
    triggered_at TIMESTAMP NOT NULL,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    status TEXT NOT NULL DEFAULT 'TRIGGERED',  -- TRIGGERED, COLLECTING, ANALYZING, DEEP_INVESTIGATION, MONITORING, COMPLETED
    current_phase TEXT NOT NULL DEFAULT 'TRIGGERED',
    risk_score REAL DEFAULT 0.0,            -- 0.0 to 1.0
    risk_level TEXT DEFAULT 'UNKNOWN',      -- LOW, MEDIUM, HIGH, CRITICAL
    confidence REAL DEFAULT 0.0,            -- AI confidence 0.0 to 1.0
    gemini_analysis TEXT,                   -- JSON of AI reasoning
    detailed_report_md TEXT,                -- Markdown report written by Gemini
    report_generated_at TIMESTAMP,          -- When detailed report was created
    summary TEXT,
    config_snapshot TEXT,                   -- JSON of settings at start
    is_active BOOLEAN DEFAULT 1,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_investigations_status ON investigations(status);
CREATE INDEX idx_investigations_pid ON investigations(pid);
CREATE INDEX idx_investigations_triggered_at ON investigations(triggered_at);
CREATE INDEX idx_investigations_is_active ON investigations(is_active);

-- Evidence collection log
CREATE TABLE IF NOT EXISTS evidence_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    evidence_type TEXT NOT NULL,            -- PROCESS_TREE, NETWORK_CONNECTIONS, FILE_SYSTEM, REGISTRY, MEMORY_SIGNATURE, EVENT_LOGS
    content TEXT NOT NULL,                  -- JSON data
    file_path TEXT,                         -- If external file stored
    importance TEXT DEFAULT 'RELEVANT',     -- INCIDENTAL, RELEVANT, CRITICAL
    content_hash TEXT,                      -- SHA256 for integrity
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE INDEX idx_evidence_investigation ON evidence_log(investigation_id);
CREATE INDEX idx_evidence_type ON evidence_log(evidence_type);
CREATE INDEX idx_evidence_importance ON evidence_log(importance);

-- Agent configuration
CREATE TABLE IF NOT EXISTS agent_config (
    id INTEGER PRIMARY KEY DEFAULT 1,
    auto_investigate BOOLEAN DEFAULT 1,
    max_concurrent_investigations INTEGER DEFAULT 3,
    max_storage_mb INTEGER DEFAULT 1024,
    cleanup_threshold_mb INTEGER DEFAULT 900,
    cleanup_amount_mb INTEGER DEFAULT 100,
    risk_threshold_low REAL DEFAULT 0.3,
    risk_threshold_medium REAL DEFAULT 0.5,
    risk_threshold_high REAL DEFAULT 0.8,
    gemini_model TEXT DEFAULT 'gemini-3-pro-preview',
    thinking_budget INTEGER DEFAULT 8000,
    enable_beta_prevention BOOLEAN DEFAULT 0,
    beta_prevention_actions TEXT,           -- JSON array
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (id = 1)                          -- Ensure single row
);

-- Insert default config
INSERT OR IGNORE INTO agent_config (id) VALUES (1);

-- Investigation snapshots for resume capability
CREATE TABLE IF NOT EXISTS investigation_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    phase TEXT NOT NULL,
    snapshot_data TEXT NOT NULL,            -- JSON of current state
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE INDEX idx_snapshots_investigation ON investigation_snapshots(investigation_id);
CREATE INDEX idx_snapshots_created ON investigation_snapshots(created_at);

-- Analyst notes
CREATE TABLE IF NOT EXISTS investigation_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT NOT NULL,
    note TEXT NOT NULL,
    created_by TEXT DEFAULT 'analyst',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE CASCADE
);

CREATE INDEX idx_notes_investigation ON investigation_notes(investigation_id);

-- System events log
CREATE TABLE IF NOT EXISTS system_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,               -- AGENT_START, AGENT_STOP, CONFIG_CHANGE, ERROR
    message TEXT,
    details TEXT,                           -- JSON
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_events_type ON system_events(event_type);
CREATE INDEX idx_events_created ON system_events(created_at);

-- Raw process events (1-hour retention for autonomous querying)
CREATE TABLE IF NOT EXISTS raw_process_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    process_path TEXT,
    parent_pid INTEGER,
    command_line TEXT,
    user_name TEXT,
    cpu_percent REAL,
    memory_mb REAL,
    network_connections TEXT,               -- JSON array
    open_files TEXT,                        -- JSON array
    threads_count INTEGER,
    status TEXT,
    event_type TEXT NOT NULL,               -- SPAWN, NETWORK, FILE_ACCESS, REGISTRY, TERMINATE
    event_details TEXT,                     -- JSON
    interval_id TEXT,                       -- Minute-level grouping (YYYY-MM-DD_HH:MM)
    collected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_raw_events_pid ON raw_process_events(pid);
CREATE INDEX idx_raw_events_collected ON raw_process_events(collected_at);
CREATE INDEX idx_raw_events_type ON raw_process_events(event_type);
CREATE INDEX idx_raw_events_process_name ON raw_process_events(process_name);
CREATE INDEX idx_raw_events_interval ON raw_process_events(interval_id);

-- Summary intervals (1-minute aggregated data for Gemini)
CREATE TABLE IF NOT EXISTS summary_intervals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interval_start TIMESTAMP NOT NULL,
    interval_end TIMESTAMP NOT NULL,
    total_processes INTEGER,
    new_processes INTEGER,
    terminated_processes INTEGER,
    suspicious_patterns TEXT,               -- JSON array
    high_cpu_processes TEXT,                -- JSON array
    high_network_processes TEXT,            -- JSON array
    unusual_file_access TEXT,               -- JSON array
    summary_text TEXT,                      -- Human-readable summary
    process_activities TEXT,                -- JSON object: per-process detailed activities
    sent_to_gemini BOOLEAN DEFAULT 0,
    gemini_response TEXT,                   -- JSON
    detailed_report_md TEXT,                -- Markdown report written by Gemini
    report_generated_at TIMESTAMP,          -- When detailed report was created
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_summary_intervals_start ON summary_intervals(interval_start);
CREATE INDEX idx_summary_intervals_sent ON summary_intervals(sent_to_gemini);

-- Gemini query log (tracks autonomous queries)
CREATE TABLE IF NOT EXISTS gemini_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_type TEXT NOT NULL,               -- QUERY_PROCESS, QUERY_TIMERANGE, QUERY_PATTERN
    query_params TEXT NOT NULL,             -- JSON
    result_count INTEGER,
    result_data TEXT,                       -- JSON
    investigation_id TEXT,                  -- Optional link to investigation
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (investigation_id) REFERENCES investigations(id) ON DELETE SET NULL
);

CREATE INDEX idx_gemini_queries_type ON gemini_queries(query_type);
CREATE INDEX idx_gemini_queries_created ON gemini_queries(created_at);

-- Short-lived processes (captured via event monitoring)
CREATE TABLE IF NOT EXISTS short_lived_processes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pid INTEGER NOT NULL,
    process_name TEXT NOT NULL,
    parent_pid INTEGER,
    detected_at TIMESTAMP NOT NULL,
    event_data TEXT,                        -- JSON with all available info
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_short_lived_pid ON short_lived_processes(pid);
CREATE INDEX idx_short_lived_name ON short_lived_processes(process_name);
CREATE INDEX idx_short_lived_detected ON short_lived_processes(detected_at);
