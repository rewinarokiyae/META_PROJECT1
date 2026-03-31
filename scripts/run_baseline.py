import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()
API_URL = "http://localhost:8000"

def get_llm_response(messages):
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    
    if provider == "groq":
        import groq
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("Missing GROQ_API_KEY environment variable")
        client = groq.Groq(api_key=api_key)
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.0
        )
        return response.choices[0].message.content.strip()
    else:
        import openai
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Missing OPENAI_API_KEY environment variable")
        client = openai.OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.0
        )
        return response.choices[0].message.content.strip()

def get_action_from_llm(obs, task_desc, action_history):
    timeline_str = "\\n".join([f"Step {t['step']}: {t['event']}" for t in obs['timeline'][-5:]])
    history_str = ", ".join(action_history) if action_history else "None"
    
    prompt = f"""
You are an advanced SRE on-call responding to an incident. Use a ReAct framework (Observe -> Think -> Act).
Task: {task_desc}

Current Observation:
- CPU: {obs['system_metrics']['cpu_percent']}%
- Memory: {obs['system_metrics']['memory_percent']}%
- Latency: {obs['system_metrics']['latency_ms']}ms
- Components: {obs['components_health']}
- Recent Logs: {obs['logs']}
- Deployment Status: {obs['deployment_status']}
- Timeline summary: 
{timeline_str}

Past Actions Taken: {history_str}

---
REDEFINE ROOT-CAUSE -> ACTION MAPPING (CRITICAL)
The agent MUST follow these exact mappings. Always prioritize log-based root cause over metrics.

CACHE FAILURE / OOM:
If logs contain "OOM", "cache node", "memory leak", "cache failure":
→ ACTION MUST BE: flush_cache
→ DO NOT choose scale_up or restart_service

DATABASE LOCK / CONNECTION ISSUE:
If logs contain "DB connections piling", "timeout waiting for downstream", "db lock":
→ ACTION MUST BE: fix_database
→ DO NOT choose scale_up or restart_service

DEPLOYMENT FAILURE:
If logs contain "deploy", "crash", "crash loop", "pods failing":
→ ACTION MUST BE: rollback_deploy

CPU SPIKE (ONLY IF NOT DB RELATED):
If logs contain "CPU spike", "background processes" AND no DB-related logs:
→ ACTION: restart_service

RESOURCE PRESSURE (ONLY WHEN NO ROOT CAUSE):
If only metrics are high (no logs):
→ ACTION: scale_up

NO ISSUE:
If metrics normal and no errors:
→ ACTION: ignore

---
STRICT SINGLE-STEP DECISION
Do NOT plan multiple steps.
Do NOT choose temporary mitigation if root cause is known.

---
DIAGNOSTIC CONTROL
Allow run_diagnostics only once.
After that, MUST act.

---
IGNORE PROTECTION
Do NOT allow ignore if memory > 80 OR latency > 150 OR errors present.

---
STRICT ACTION CONSTRAINT
Available Actions:
* restart_service
* rollback_deploy
* scale_up
* check_logs
* run_diagnostics
* fix_database
* flush_cache
* ignore

You MUST choose exactly one action from the list above.

---
OUTPUT FORMAT
Root Cause Detected: <type>
THOUGHT: (short reasoning, max 2 lines)
ACTION: <one valid action>
"""
    
    try:
        content = get_llm_response([{"role": "user", "content": prompt}])
    except Exception as e:
        return f"LLM Error: {str(e)}", "run_diagnostics"
    
    # parse out action
    action_str = ""
    root_cause_str = "Unknown"
    try:
        for line in content.split('\n'):
            if line.startswith("Root Cause Detected:"):
                root_cause_str = line.split("Root Cause Detected:")[1].strip()
            if line.startswith("ACTION:") or line.startswith("ACTION: "):
                action_str = line.split("ACTION:")[1].strip()
    except Exception:
        pass
        
    allowed_actions = [
        "restart_service",
        "rollback_deploy",
        "scale_up",
        "check_logs",
        "run_diagnostics",
        "fix_database",
        "flush_cache",
        "ignore"
    ]
    
    if action_str not in allowed_actions:
        print(f"Invalid action '{action_str}' replaced with 'run_diagnostics'")
        action_str = "run_diagnostics"

    print(f"Root Cause Detected: {root_cause_str}")
    print(f"Action Selected: {action_str}")

    return content, action_str

def play_episode(task_id, task_desc):
    print(f"\\n{'='*40}\\n--- Starting Task: {task_id} ---\\n{'='*40}")
    
    # Reset with seed for reproducibility
    res = requests.post(f"{API_URL}/reset", json={"task_id": task_id, "seed": 42})
    if res.status_code != 200:
        print(f"Failed to reset: {res.text}")
        return
        
    obs = res.json()
    done = False
    step = 0
    action_history = []
    
    while not done and step < 15:
        step += 1
        
        # Get action
        thought_action_full, action_str = get_action_from_llm(obs, task_desc, action_history)
        print(f"\\n[Step {step}] LLM Output:\\n{thought_action_full}")
        
        action_payload = {"action_type": action_str}
        
        # Step
        res = requests.post(f"{API_URL}/step", json=action_payload)
        if res.status_code != 200:
            print(f"Failed step: {res.text}")
            break
            
        step_data = res.json()
        obs = step_data["observation"]
        reward = step_data["reward"]
        done = step_data["done"]
        info = step_data["info"]
        
        action_history = info["action_history"]
        cumulative_reward = info["cumulative_reward"]
        
        print(f"   Reward: {reward['value']} ({reward['reason']}) | Cumulative: {cumulative_reward:.2f}")
        if done:
            print(f"\\n>>> Episode Done. Resolved: {info['resolved']}")
            break
            
        time.sleep(1)
        
    # Grade
    grader_payload = {
        "timeline": obs["timeline"],
        "action_history": action_history,
        "is_resolved": info.get("resolved", False),
        "task_id": task_id
    }
    grade_res = requests.post(f"{API_URL}/grader", json=grader_payload)
    score = grade_res.json().get("score", 0.0)
    
    print(f"\\n*** Final Output ***\\nTask {task_id} Score: {score}/1.0\\nTotal steps: {step}\\nCumulative Reward: {info.get('cumulative_reward', 0):.2f}")

def main():
    try:
        tasks = requests.get(f"{API_URL}/tasks").json()
    except requests.exceptions.ConnectionError:
        print(f"Could not connect to API at {API_URL}. Ensure it is running.")
        return
        
    for task_id, task_info in tasks.items():
        try:
            play_episode(task_id, task_info["description"])
        except ValueError as ve:
            print(f"\\nInitialization Error: {ve}")
            break

if __name__ == "__main__":
    main()
