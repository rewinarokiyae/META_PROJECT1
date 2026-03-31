from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

class Observation(BaseModel):
    system_metrics: Dict[str, float]
    components_health: Dict[str, str]
    logs: List[str]
    deployment_status: str
    region_info: str
    timeline: List[Dict[str, Any]]

class Action(BaseModel):
    action_type: str
    target: Optional[str] = None
    
class Reward(BaseModel):
    value: float
    reason: str
