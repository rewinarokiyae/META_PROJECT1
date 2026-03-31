from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

from app.env import AIOpsEnv
from app.models import Action, Observation, Reward
from app.tasks import TASKS
from app.grader import grade_episode

app = FastAPI(title="Advanced AI Operations War Room Environment API")
env = AIOpsEnv()

class ResetRequest(BaseModel):
    task_id: str = "easy"
    seed: Optional[int] = None

class StepResponse(BaseModel):
    observation: Observation
    reward: Reward
    done: bool
    info: Dict[str, Any]

class GraderRequest(BaseModel):
    timeline: List[Dict[str, Any]]
    action_history: List[str]
    is_resolved: bool
    task_id: str

class GraderResponse(BaseModel):
    score: float

@app.post("/reset", response_model=Observation)
async def reset_env(req: ResetRequest):
    if req.task_id not in TASKS:
        raise HTTPException(status_code=400, detail="Invalid task_id")
    return env.reset(req.task_id, req.seed)

@app.post("/step", response_model=StepResponse)
async def step_env(action: Action):
    obs, reward, done, info = env.step(action)
    return StepResponse(
        observation=obs,
        reward=reward,
        done=done,
        info=info
    )

@app.get("/state", response_model=Observation)
async def get_state():
    return env.state()

@app.get("/tasks")
async def get_tasks():
    return TASKS

@app.post("/grader", response_model=GraderResponse)
async def grade_performance(req: GraderRequest):
    task = TASKS.get(req.task_id)
    if not task:
        raise HTTPException(status_code=400, detail="Invalid task_id")
        
    score = grade_episode(req.timeline, req.action_history, req.is_resolved, task["optimal_steps"])
    return GraderResponse(score=score)

@app.post("/baseline")
async def run_baseline_agent():
    import subprocess
    import sys
    try:
        result = subprocess.run([sys.executable, "scripts/run_baseline.py"], capture_output=True, text=True)
        return {"output": result.stdout, "error": result.stderr}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
