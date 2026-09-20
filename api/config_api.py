"""
Configuration API Endpoints
"""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional, List

from api.dependencies import get_state_manager

router = APIRouter(prefix="/config", tags=["configuration"])


class ConfigResponse(BaseModel):
    """Configuration response model"""
    auto_investigate: bool
    max_concurrent_investigations: int
    max_storage_mb: int
    cleanup_threshold_mb: int
    cleanup_amount_mb: int
    risk_threshold_low: float
    risk_threshold_medium: float
    risk_threshold_high: float
    gemini_model: str
    thinking_budget: int
    enable_beta_prevention: bool


class ConfigUpdate(BaseModel):
    """Configuration update model"""
    auto_investigate: Optional[bool] = None
    max_concurrent_investigations: Optional[int] = None
    max_storage_mb: Optional[int] = None
    cleanup_threshold_mb: Optional[int] = None
    cleanup_amount_mb: Optional[int] = None
    risk_threshold_low: Optional[float] = None
    risk_threshold_medium: Optional[float] = None
    risk_threshold_high: Optional[float] = None
    gemini_model: Optional[str] = None
    thinking_budget: Optional[int] = None
    enable_beta_prevention: Optional[bool] = None


class ProfileInfo(BaseModel):
    """Investigation profile info"""
    id: str
    name: str
    description: str
    log_retention_hours: float
    investigation_depth: str


@router.get("/", response_model=ConfigResponse)
async def get_config(state_manager = Depends(get_state_manager)):
    """Get current configuration"""
    async with state_manager.db.execute(
        "SELECT * FROM agent_config WHERE id = 1"
    ) as cursor:
        row = await cursor.fetchone()
        if row:
            return dict(row)
    
    # Return defaults if not found
    return {
        "auto_investigate": True,
        "max_concurrent_investigations": 3,
        "max_storage_mb": 1024,
        "cleanup_threshold_mb": 900,
        "cleanup_amount_mb": 100,
        "risk_threshold_low": 0.3,
        "risk_threshold_medium": 0.5,
        "risk_threshold_high": 0.8,
        "gemini_model": "gemini-3-pro-preview",
        "thinking_budget": 8000,
        "enable_beta_prevention": False
    }


@router.post("/")
async def update_config(
    config: ConfigUpdate,
    state_manager = Depends(get_state_manager)
):
    """Update configuration"""
    # Build update query
    updates = {}
    for field, value in config.dict(exclude_unset=True).items():
        if value is not None:
            updates[field] = value
    
    if updates:
        set_clauses = [f"{k} = ?" for k in updates.keys()]
        values = list(updates.values())
        
        query = f"UPDATE agent_config SET {', '.join(set_clauses)}, updated_at = CURRENT_TIMESTAMP WHERE id = 1"
        await state_manager.db.execute(query, values)
        await state_manager.db.commit()
        
        # Log config change
        await state_manager.log_system_event(
            "CONFIG_CHANGE",
            "Configuration updated",
            updates
        )
    
    return {"message": "Configuration updated", "updates": updates}


@router.post("/test-gemini")
async def test_gemini_connection():
    """Test Gemini 2.5 Flash connection"""
    try:
        from agent.config import load_config
        from agent.gemini_client import GeminiClient
        
        config = load_config()
        gemini = GeminiClient(config)
        
        # Simple test prompt
        test_prompt = """Respond with valid JSON only:
{
  "status": "connected",
  "model": "gemini-3-pro-preview",
  "message": "Connection successful"
}"""
        
        from google.genai import types
        response = gemini.client.models.generate_content(
            model=gemini.model_name,
            contents=test_prompt,
            config=types.GenerateContentConfig(
                temperature=1.0,
                response_mime_type="application/json"
            )
        )
        
        import json
        result = json.loads(response.text)
        
        return {
            "success": True,
            "model": gemini.model_name,
            "response": result,
            "message": "Gemini 2.5 Flash connection successful!"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Gemini connection failed: {str(e)}"
        }


@router.get("/profiles", response_model=List[ProfileInfo])
async def list_profiles():
    """List available investigation profiles"""
    profiles = [
        {
            "id": "quick_triage",
            "name": "Quick Triage",
            "description": "Fast analysis for demos and low-risk environments",
            "log_retention_hours": 0.5,
            "investigation_depth": "QUICK"
        },
        {
            "id": "standard_soc",
            "name": "Standard SOC",
            "description": "Balanced approach for production workstations",
            "log_retention_hours": 6.0,
            "investigation_depth": "STANDARD"
        },
        {
            "id": "deep_hunt",
            "name": "Deep Hunt",
            "description": "Comprehensive investigation for APT detection",
            "log_retention_hours": 24.0,
            "investigation_depth": "DEEP"
        },
        {
            "id": "training_mode",
            "name": "Training Mode",
            "description": "Manual confirmation at each step for learning",
            "log_retention_hours": 6.0,
            "investigation_depth": "STANDARD"
        }
    ]
    
    return profiles


@router.post("/profiles/{profile_id}/apply")
async def apply_profile(
    profile_id: str,
    state_manager = Depends(get_state_manager)
):
    """Apply investigation profile"""
    profiles = {
        "quick_triage": {
            "log_retention_hours": 0.5,
            "investigation_depth": "QUICK"
        },
        "standard_soc": {
            "log_retention_hours": 6.0,
            "investigation_depth": "STANDARD"
        },
        "deep_hunt": {
            "log_retention_hours": 24.0,
            "investigation_depth": "DEEP"
        },
        "training_mode": {
            "log_retention_hours": 6.0,
            "investigation_depth": "STANDARD"
        }
    }
    
    if profile_id not in profiles:
        return {"error": "Profile not found"}, 404
    
    profile = profiles[profile_id]
    
    # Update config
    await state_manager.db.execute("""
        UPDATE agent_config 
        SET log_retention_hours = ?, investigation_depth = ?, updated_at = CURRENT_TIMESTAMP
        WHERE id = 1
    """, (profile["log_retention_hours"], profile["investigation_depth"]))
    await state_manager.db.commit()
    
    await state_manager.log_system_event(
        "CONFIG_CHANGE",
        f"Applied profile: {profile_id}",
        profile
    )
    
    return {"message": f"Profile {profile_id} applied", "config": profile}
