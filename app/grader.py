def grade_episode(timeline: list, action_history: list, is_resolved: bool, optimal_steps: int) -> float:
    # Trajectory-aware grading: 40% correctness, 30% efficiency, 30% reasoning
    if not is_resolved:
        return 0.0
        
    correctness_score = 0.4
    
    # Efficiency calculation (30%)
    efficiency_score = 0.3
    extra_steps = max(0, len(action_history) - optimal_steps)
    if extra_steps > 0:
        efficiency_score -= min(0.3, extra_steps * 0.05)
        
    # Reasoning quality calculation (30%)
    reasoning_score = 0.3
    
    # Good reasoning = diagnostic before fixes, no spamming random actions
    fixes = ["fix_database", "flush_cache", "rollback_deploy", "restart_service"]
    diagnostics = ["run_diagnostics", "check_logs"]
    
    has_diagnostic = False
    premature_fixes = 0
    redundant_diagnostics = 0
    
    for action in action_history:
        if action in diagnostics:
            if has_diagnostic:
                redundant_diagnostics += 1
            has_diagnostic = True
        elif action in fixes:
            if not has_diagnostic:
                premature_fixes += 1
                
    reasoning_score -= min(0.15, premature_fixes * 0.1)
    reasoning_score -= min(0.15, redundant_diagnostics * 0.05)
    
    total_score = correctness_score + max(0.0, efficiency_score) + max(0.0, reasoning_score)
    return round(max(0.0, min(1.0, total_score)), 2)
