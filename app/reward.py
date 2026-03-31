def calculate_reward(action_type: str, action_data: dict, is_resolved: bool, action_history: list, step_count: int, state_before: dict, state_after: dict) -> tuple[float, str]:
    reward = 0.0
    reason = []
    
    correct_action = action_data.get("correct_action", False)
    diagnostics_run = action_data.get("diagnostics_run", False)
    invalid_action = action_data.get("invalid_action", False)
    
    if invalid_action:
        reward -= 0.5
        reason.append("Invalid or hallucinated action taken")
        
    elif diagnostics_run:
        if action_history.count(action_type) > 2:
            reward -= 0.2
            reason.append("Redundant diagnostic actions")
        elif step_count <= 2:
            reward += 0.2
            reason.append("Useful early diagnostic action")
        else:
            reward += 0.1
            reason.append("Diagnostic action")
            
    elif correct_action:
        reward += 0.4
        reason.append("Correct fix applied")
        if is_resolved:
            reward += 0.1
            if step_count <= 4:
                reward += 0.1
                reason.append("Efficient resolution sequence")
                
    elif action_type == "ignore":
        mem_high = state_before["system_metrics"]["memory_percent"] > 85.0
        lat_high = state_before["system_metrics"]["latency_ms"] > 200.0
        has_error = any(kw in log for log in state_before["logs"] for kw in ["ERROR", "failed", "timeout", "OOM", "crashing"])
        
        if mem_high or lat_high or has_error:
            reward -= 0.3
            reason.append("WARNING: Agent ignored unresolved issue")
        else:
            reward -= 0.5
            reason.append("Ignored worsening system state")
        
    else:
        # Check if it was a misleading/wrong action
        if action_type in ["scale_up", "restart_service"] and not correct_action:
            reward -= 0.1
            reason.append("Action mitigated briefly but didn't fix root cause")
            
        else:
            reward -= 0.3
            reason.append("Misleading or wrong action taken")
            
    # Check degradation
    latency_diff = state_after["system_metrics"]["latency_ms"] - state_before["system_metrics"]["latency_ms"]
    if latency_diff > 100:
        reward -= 0.2
        reason.append("System latency severely degraded")
        
    if not reason:
        reason.append("No immediate reward impact")
        
    return reward, " | ".join(reason)
