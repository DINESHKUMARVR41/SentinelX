"""
Configuration management for PROCSee agent
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings
import yaml


class GeminiConfig(BaseModel):
    """Gemini 2.5 Flash configuration"""
    model_config = {"protected_namespaces": ()}
    
    api_key: str
    model_pro: str = "gemini-2.5-flash"
    thinking_level: str = "high"  # low or high
    max_tokens: int = 1000000
    temperature: float = 1.0  # Keep at 1.0 for Gemini 3


class RiskThresholds(BaseModel):
    """Risk scoring thresholds"""
    low: float = 0.3
    medium: float = 0.5
    high: float = 0.8


class TriggerConfig(BaseModel):
    """Process trigger configuration"""
    unsigned_executable: bool = True
    temp_spawn: bool = True
    browser_spawns_shell: bool = True
    rapid_network_activity: bool = True
    registry_persistence: bool = True
    memory_access_attempt: bool = True


class AgentConfig(BaseModel):
    """Agent behavior configuration"""
    log_retention_hours: float = 6.0
    investigation_depth: str = "STANDARD"  # QUICK, STANDARD, DEEP
    auto_investigate: bool = True
    max_concurrent_investigations: int = 3
    checkpoint_interval_seconds: int = 60


class BetaPreventionConfig(BaseModel):
    """Beta prevention features configuration"""
    enabled: bool = False
    allowed_actions: list[str] = ["suspend_process", "network_isolation", "file_quarantine"]
    exclude_system_processes: bool = True
    require_confirmation: bool = True
    auto_rollback_minutes: int = 5


class PROCSeeConfig(BaseSettings):
    """Main PROCSee configuration"""
    model_config = {
        "extra": "ignore",
        "protected_namespaces": (),
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }
    
    # Gemini 2.5 Flash
    gemini_api_key: str = Field(default="", alias="GEMINI_API_KEY")  # empty => demo mode (no live AI)
    gemini_model_pro: str = Field(default="gemini-2.5-flash", alias="GEMINI_MODEL_PRO")
    
    # Paths
    database_path: str = Field(default="./database/procsee.db", alias="DATABASE_PATH")
    evidence_storage_path: str = Field(default="./evidence_storage", alias="EVIDENCE_STORAGE_PATH")
    
    # Agent
    log_retention_hours: float = Field(default=6.0, alias="LOG_RETENTION_HOURS")
    investigation_depth: str = Field(default="STANDARD", alias="INVESTIGATION_DEPTH")
    max_concurrent_investigations: int = Field(default=3, alias="MAX_CONCURRENT_INVESTIGATIONS")
    auto_investigate: bool = Field(default=False, alias="AUTO_INVESTIGATE")
    
    # Beta
    enable_beta_prevention: bool = Field(default=False, alias="ENABLE_BETA_PREVENTION")

    # Live Windows monitoring is opt-in so adding an API key does not start
    # continuous AI analysis and consume free-tier quota unexpectedly.
    enable_live_monitoring: bool = Field(default=False, alias="ENABLE_LIVE_MONITORING")

    @property
    def live_ai_enabled(self) -> bool:
        k = (self.gemini_api_key or "").strip()
        return bool(k) and not k.startswith("your_")


def load_config() -> PROCSeeConfig:
    """Load configuration from environment and config files"""
    return PROCSeeConfig()


def load_yaml_config(path: str = "config.yaml") -> Dict[str, Any]:
    """Load YAML configuration file"""
    config_path = Path(path)
    if not config_path.exists():
        return {}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f) or {}
