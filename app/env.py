import uuid
from typing import Tuple, Dict, Any, Optional
from app.models import Observation, Action, Reward
from app.simulator import Simulator
from app.reward import calculate_reward
from app.tasks import TASKS

class AIOpsEnv:
    def __init__(self):
        self.simulator = Simulator()
        self.action_history = []
        self.session_id = str(uuid.uuid4())
        self.current_task = None
        self.step_count = 0
        self.max_steps = 15
        self.cumulative_reward = 0.0

    def reset(self, task_id="easy", seed: Optional[int] = None) -> Observation:
        self.action_history = []
        self.step_count = 0
        self.cumulative_reward = 0.0
        self.current_task = TASKS.get(task_id, TASKS["easy"])
        
        self.simulator.reset(incident_type=self.current_task["incident_type"], seed=seed)
        state = self.simulator.get_state()
        return Observation(**state)

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Dict[str, Any]]:
        self.step_count += 1
        self.action_history.append(action.action_type)
        
        state_before = self.simulator.get_state()
        action_data = self.simulator.step(action.action_type)
        state_after = self.simulator.get_state()
        
        # Calculate Reward
        reward_val, reason = calculate_reward(
            action.action_type, 
            action_data, 
            self.simulator.is_resolved,
            self.action_history,
            self.step_count,
            state_before,
            state_after
        )
        self.cumulative_reward += reward_val
        
        reward = Reward(value=reward_val, reason=reason)
        
        # Done condition
        done = self.simulator.is_resolved or self.step_count >= self.max_steps
        
        obs = Observation(**state_after)
        
        info = {
            "resolved": self.simulator.is_resolved,
            "step_count": self.step_count,
            "action_history": self.action_history,
            "cumulative_reward": self.cumulative_reward
        }
        
        return obs, reward, done, info

    def state(self) -> Observation:
        return Observation(**self.simulator.get_state())
